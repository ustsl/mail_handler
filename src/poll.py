import asyncio
from typing import Callable, Awaitable
from src.email_worker.schema import MailCheckSettings


async def poll_mail(
    settings: MailCheckSettings,
    worker: Callable[..., Awaitable[None]],
    rules: object,
    interval: int = 10,
):
    """
    Periodically calls an ASYNCHRONOUS worker function.
    """
    while True:
        try:
            await worker(settings=settings, rules=rules)
        except Exception as e:
            print(f"[ERROR] in poller for {settings.user}: {e}")

        await asyncio.sleep(interval)
