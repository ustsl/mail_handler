import os
import json
import aio_pika

from src.query_worker.request_sender import send_request
from src.settings import RABBIT_URL
from src.outbox.infra import (
    EXCHANGE_MAIN,
    EXCHANGE_DLX,
    QUEUE_MAIN,
    ROUTING_MAIN,
    BACKOFF_SCHEDULE,
    ensure_infra,
    rkey_retry,
)

MAX_RETRIES = int(os.getenv("OUTBOUND_MAX_RETRIES", "8"))


def _next_ttl(n: int) -> int:
    i = max(0, min(n - 1, len(BACKOFF_SCHEDULE) - 1))
    return BACKOFF_SCHEDULE[i]


async def _republish_retry(ch: aio_pika.Channel, payload: dict) -> None:
    ttl = _next_ttl(int(payload.get("retry_count", 0)))
    dlx = await ch.get_exchange(EXCHANGE_DLX)
    msg = aio_pika.Message(
        body=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
        content_type="application/json",
    )
    await dlx.publish(msg, routing_key=rkey_retry(ttl))


async def _handle(msg: aio_pika.IncomingMessage) -> None:
    async with msg.process(requeue=False):
        payload = json.loads(msg.body.decode("utf-8"))
        try:
            if payload.get("kind") != "json":
                return
            await send_request(
                method=payload["method"],
                url=payload["url"],
                headers=payload["headers"],
                data=payload["json"],
            )
        except Exception:
            payload["retry_count"] = int(payload.get("retry_count", 0)) + 1
            if payload["retry_count"] > MAX_RETRIES:
                return
            await _republish_retry(msg.channel, payload)


async def main() -> None:
    conn = await aio_pika.connect(RABBIT_URL)
    async with conn:
        ch = await conn.channel()
        await ensure_infra(ch)
        q = await ch.get_queue(QUEUE_MAIN)
        await q.consume(_handle, no_ack=False)
        await __import__("asyncio").Future()
