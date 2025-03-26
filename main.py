import asyncio

from src.email_worker.poll import poll_mail
from src.settings import mail_settings


async def main():
    print("Launch email asyncio server...")
    await poll_mail(settings=mail_settings, interval=10)


if __name__ == "__main__":
    asyncio.run(main())
