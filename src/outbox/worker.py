import os
import json
import aio_pika

from src.query_worker.request_sender import send_request
from src.settings import RABBIT_URL

EXCHANGE_MAIN = "outbound_http.exchange"
EXCHANGE_DLX = f"{EXCHANGE_MAIN}.dlx"
QUEUE_MAIN = "outbound_http"
ROUTING_MAIN = "outbound_http"
BACKOFF_SCHEDULE = [30, 120, 600, 3600]
MAX_RETRIES = int(os.getenv("OUTBOUND_MAX_RETRIES", "8"))


def _rkey_retry(ttl: int) -> str:
    return f"{ROUTING_MAIN}.retry.{ttl}s"


def _next_ttl(n: int) -> int:
    i = max(0, min(n - 1, len(BACKOFF_SCHEDULE) - 1))
    return BACKOFF_SCHEDULE[i]


async def _ensure_infra(ch: aio_pika.Channel) -> None:
    ex = await ch.declare_exchange(
        EXCHANGE_MAIN, aio_pika.ExchangeType.DIRECT, durable=True
    )
    dlx = await ch.declare_exchange(
        EXCHANGE_DLX, aio_pika.ExchangeType.DIRECT, durable=True
    )
    await ch.declare_queue(
        QUEUE_MAIN, durable=True, arguments={"x-dead-letter-exchange": EXCHANGE_DLX}
    )
    await (await ch.get_queue(QUEUE_MAIN)).bind(ex, ROUTING_MAIN)
    for ttl in BACKOFF_SCHEDULE:
        q = f"{QUEUE_MAIN}.retry.{ttl}s"
        await ch.declare_queue(
            q,
            durable=True,
            arguments={
                "x-message-ttl": ttl * 1000,
                "x-dead-letter-exchange": EXCHANGE_MAIN,
                "x-dead-letter-routing-key": ROUTING_MAIN,
            },
        )
        await (await ch.get_queue(q)).bind(dlx, _rkey_retry(ttl))


async def _republish_retry(ch: aio_pika.Channel, payload: dict) -> None:
    ttl = _next_ttl(int(payload.get("retry_count", 0)))
    dlx = await ch.get_exchange(EXCHANGE_DLX)
    msg = aio_pika.Message(
        body=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        content_type="application/json",
    )
    await dlx.publish(msg, routing_key=_rkey_retry(ttl))


async def _handle(msg: aio_pika.IncomingMessage) -> None:
    async with msg.process(requeue=False):
        payload = json.loads(msg.body.decode("utf-8"))
        try:
            if payload.get("kind") != "json":
                return
            resp = await send_request(
                method=payload["method"],
                url=payload["url"],
                headers=payload["headers"],
                data=payload["json"],
            )
            # print(f"[OK] {payload['method']} {payload['url']} -> {len(resp)} bytes")
        except Exception:
            payload["retry_count"] = int(payload.get("retry_count", 0)) + 1
            if payload["retry_count"] > MAX_RETRIES:
                return
            await _republish_retry(msg.channel, payload)


async def main() -> None:
    conn = await aio_pika.connect(RABBIT_URL)
    async with conn:
        ch = await conn.channel()
        await _ensure_infra(ch)
        q = await ch.get_queue(QUEUE_MAIN)
        await q.consume(_handle, no_ack=False)
        await __import__("asyncio").Future()
