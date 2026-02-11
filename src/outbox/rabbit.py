import asyncio

import aio_pika

from src.settings import RABBIT_URL


async def connect_rabbitmq(retry_delay: int = 3) -> aio_pika.RobustConnection:
    """
    Connect to RabbitMQ with infinite retries.
    This prevents startup race conditions when broker is still booting.
    """
    while True:
        try:
            return await aio_pika.connect_robust(RABBIT_URL)
        except Exception as exc:
            print(f"RabbitMQ not ready: {exc}. Retry in {retry_delay}s.")
            await asyncio.sleep(retry_delay)
