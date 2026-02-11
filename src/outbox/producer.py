import json
from typing import Dict, Optional

import aio_pika

from src.outbox.infra import EXCHANGE_MAIN, ROUTING_MAIN, ensure_infra
from src.outbox.rabbit import connect_rabbitmq
from src.settings import RABBIT_URL


async def enqueue_json_request(
    method: str, url: str, headers: Optional[Dict[str, str]], json_body: Dict
) -> None:
    if not RABBIT_URL:
        return

    payload = {
        "kind": "json",
        "method": method,
        "url": url,
        "headers": headers or {},
        "json": json_body,
        "retry_count": 0,
    }

    conn = await connect_rabbitmq()
    async with conn:
        ch = await conn.channel(publisher_confirms=True)
        await ensure_infra(ch)
        ex = await ch.get_exchange(EXCHANGE_MAIN)
        msg = aio_pika.Message(
            body=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
            delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            content_type="application/json",
        )
        await ex.publish(msg, routing_key=ROUTING_MAIN)
