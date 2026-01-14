import asyncio

from src.email_worker.check_email import check_mail
from src.outbox.worker import main as queue_worker_main
from src.poll import poll_mail
from src.rules.apointment_rules import rules as appointment_rules
from src.rules.insurance_rules import rules as insurance_rules
from src.settings import appointment_mail_settings, insurance_mail_settings

RETRY_DELAY = 30


async def run_task(name, func, **kwargs):
    """Запускает задачу, при падении пытается поднять её снова."""
    while True:
        try:
            await func(**kwargs)
        except Exception as e:
            print(f"[КРИТИЧЕСКАЯ ОШИБКА] '{name}' упал: {e}")
            print(f"Перезапуск через {RETRY_DELAY} секунд...")
            await asyncio.sleep(RETRY_DELAY)


async def main():
    print("Запуск всех процессов...")

    work_poller_task = asyncio.create_task(
        run_task(
            "work_poller",
            poll_mail,
            settings=appointment_mail_settings,
            worker=check_mail,
            rules=appointment_rules,
            interval=10,
        )
    )

    support_poller_task = asyncio.create_task(
        run_task(
            "support_poller",
            poll_mail,
            settings=insurance_mail_settings,
            worker=check_mail,
            rules=insurance_rules,
            interval=11,
        )
    )

    queue_task = asyncio.create_task(run_task("queue_worker", queue_worker_main))

    await asyncio.gather(
        work_poller_task,
        support_poller_task,
        queue_task,
    )


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nСервер остановлен пользователем.")
