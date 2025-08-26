import aio_pika

EXCHANGE_MAIN = "outbound_http.exchange"
EXCHANGE_DLX = f"{EXCHANGE_MAIN}.dlx"
QUEUE_MAIN = "outbound_http"
ROUTING_MAIN = "outbound_http"
BACKOFF_SCHEDULE = [30, 120, 600, 3600]


def rkey_retry(ttl: int) -> str:
    return f"{ROUTING_MAIN}.retry.{ttl}s"


async def ensure_infra(ch: aio_pika.Channel) -> None:
    ex = await ch.declare_exchange(
        EXCHANGE_MAIN, aio_pika.ExchangeType.DIRECT, durable=True
    )
    dlx = await ch.declare_exchange(
        EXCHANGE_DLX, aio_pika.ExchangeType.DIRECT, durable=True
    )

    await ch.declare_queue(
        QUEUE_MAIN,
        durable=True,
        arguments={"x-dead-letter-exchange": EXCHANGE_DLX},
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
        await (await ch.get_queue(q)).bind(dlx, rkey_retry(ttl))
