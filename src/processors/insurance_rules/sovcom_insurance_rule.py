import re
from bs4 import BeautifulSoup
from aiohttp import FormData

from src.processors.utils.form_data_finalize import finalize_and_add_patients_json
from src.processors.utils.formatters import clean_message_text


def sovcom_insurance_rule(
    content: str | None,
    subject: str,
    sender: str,
    attachments: list[tuple[str, bytes]] | None,
) -> FormData:
    """
    Обрабатывает письма от «Совкомбанк Страхование».
    Извлекает данные о пациенте из тела письма.
    """
    form_data = FormData()
    patients_data = []

    cleaned_text = ""
    if content:
        soup = BeautifulSoup(content, "html.parser")

        for style in soup.find_all("style"):
            style.decompose()

        raw_text = soup.get_text(separator="\n")
        cleaned_text = clean_message_text(raw_text)

    form_data.add_field("insurance_email_sender", sender)
    form_data.add_field("subject", subject)
    form_data.add_field("original_message", cleaned_text)

    if cleaned_text:

        pattern = (
            r"([А-Яа-яЁё]+\s+[А-Яа-яЁё]+\s+[А-Яа-яЁё]+),\s*номер полиса\s*([\d\-/]+)"
        )
        match = re.search(pattern, cleaned_text)

        if match:
            patient_fio = match.group(1).strip()
            policy_number = match.group(2).strip()

            print(
                f"Из тела письма извлечено: ФИО='{patient_fio}', Полис='{policy_number}'"
            )

            patients_data.append(
                {
                    "patient_name": patient_fio,
                    "insurance_policy_number": policy_number,
                }
            )

    if attachments:
        for filename, file_bytes in attachments:
            form_data.add_field(
                "files",
                file_bytes,
                filename=filename,
            )

    finalize_and_add_patients_json(form_data, patients_data)

    return form_data
