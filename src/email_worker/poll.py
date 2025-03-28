import asyncio

from src.email_worker.check_email import check_mail
from src.email_worker.schema import MailCheckSettings
from src.rules import rules


async def poll_mail(settings: MailCheckSettings, interval=10):
    """MAIL POOLING"""
    while True:
        # Выполняем синхронную функцию check_mail в отдельном потоке и передаём settings
        await asyncio.to_thread(check_mail, settings, rules)
        await asyncio.sleep(interval)
