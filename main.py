import asyncio

from src.email_worker.check_email import check_mail
from src.poll import poll_mail
from src.rules.apointment_rules import rules as appointment_rules
from src.rules.insurance_rules import rules as insurance_rules
from src.settings import (
    appointment_mail_settings,
    insurance_mail_settings,
)


async def main():

    print("Launch email asyncio server...")

    work_poller = poll_mail(
        settings=appointment_mail_settings,
        worker=check_mail,
        rules=appointment_rules,
        interval=10,
    )
    support_poller = poll_mail(
        settings=insurance_mail_settings,
        worker=check_mail,
        rules=insurance_rules,
        interval=11,
    )

    await asyncio.gather(work_poller, support_poller)


if __name__ == "__main__":
    asyncio.run(main())
