import json
import aio_pika
from typing import Optional, Dict

from src.settings import RABBIT_URL

EXCHANGE_MAIN = "outbound_http.exchange"
EXCHANGE_DLX = f"{EXCHANGE_MAIN}.dlx"
QUEUE_MAIN = "outbound_http"
ROUTING_MAIN = "outbound_http"
BACKOFF_SCHEDULE = [30, 120, 600, 3600]


def _rkey_retry(ttl: int) -> str:
    return f"{ROUTING_MAIN}.retry.{ttl}s"


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


async def enqueue_json_request(
    method: str, url: str, headers: Optional[Dict[str, str]], json_body: Dict
) -> None:
    payload = {
        "kind": "json",
        "method": method,
        "url": url,
        "headers": headers or {},
        "json": json_body,
        "retry_count": 0,
    }
    conn = await aio_pika.connect(RABBIT_URL)
    async with conn:
        ch = await conn.channel(publisher_confirms=True)
        await _ensure_infra(ch)
        ex = await ch.get_exchange(EXCHANGE_MAIN)
        msg = aio_pika.Message(
            body=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            content_type="application/json",
        )
        await ex.publish(msg, routing_key=ROUTING_MAIN)
