import asyncio

from src.email_worker.schema import MailCheckSettings


async def poll_mail(settings: MailCheckSettings, worker, rules, interval=10):
    """MAIL POOLING"""
    while True:
        # Выполняем синхронную функцию check_mail в отдельном потоке и передаём settings
        await asyncio.to_thread(worker, settings, rules)
        await asyncio.sleep(interval)
