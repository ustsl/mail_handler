import asyncio

# Ваши импорты
from src.email_worker.check_email import check_mail
from src.poll import poll_mail
from src.rules.apointment_rules import rules as appointment_rules
from src.rules.insurance_rules import rules as insurance_rules
from src.settings import (
    appointment_mail_settings,
    insurance_mail_settings,
)

RETRY_DELAY = 60


async def run_poller_safely(name, poll_func, **kwargs):
    while True:
        try:
            await poll_func(**kwargs)
        except Exception as e:
            print(f"[КРИТИЧЕСКАЯ ОШИБКА] Задача '{name}' упала с ошибкой: {e}")
            print(f"Попробую перезапустить через {RETRY_DELAY} секунд...")
            await asyncio.sleep(RETRY_DELAY)


async def main():
    print("Launch email asyncio server...")

    work_poller_task = asyncio.create_task(
        run_poller_safely(
            name="work_poller",
            poll_func=poll_mail,
            settings=appointment_mail_settings,
            worker=check_mail,
            rules=appointment_rules,
            interval=10,
        )
    )

    support_poller_task = asyncio.create_task(
        run_poller_safely(
            name="support_poller",
            poll_func=poll_mail,
            settings=insurance_mail_settings,
            worker=check_mail,
            rules=insurance_rules,
            interval=11,
        )
    )

    await asyncio.gather(work_poller_task, support_poller_task)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nСервер остановлен.")
