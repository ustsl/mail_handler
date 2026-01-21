import re

from aiohttp import FormData
from bs4 import BeautifulSoup
from striprtf.striprtf import rtf_to_text

from src.processors.utils.date_helpers import extract_date_range
from src.processors.utils.form_data_finalize import \
    finalize_and_add_patients_json
from src.processors.utils.formatters import clean_message_text


def alfa_insurance_rule(
    content: str | None,
    subject: str,
    sender: str,
    attachments: list[tuple[str, bytes]] | None,
) -> FormData:

    form_data = FormData()

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

    patients_data = []

    if attachments:
        for filename, file_bytes in attachments:
            form_data.add_field(
                "files",
                file_bytes,
                filename=filename,
            )

            if filename.lower().endswith(".rtf"):
                try:
                    rtf_content = file_bytes.decode("cp1251")
                    plain_text = rtf_to_text(rtf_content)

                    def extract_data(pattern, text, default_message="не найдено"):
                        match = re.search(pattern, text)
                        if match:
                            return match.group(1).strip()
                        return default_message

                    fio_pattern = r"Застрахованный:\s*(.*?)\n"
                    policy_pattern = r"Страховой полис:\s*(.*?)\n"

                    patient_fio = extract_data(fio_pattern, plain_text)
                    policy_number = extract_data(policy_pattern, plain_text)

                    date_from, date_to = extract_date_range(
                        plain_text,
                        r"Срок\s+действия\s+полиса\s+с\s+(\d{2}\.\d{2}\.\d{4})\s+по\s+(\d{2}\.\d{2}\.\d{4})",
                        flags=re.IGNORECASE,
                    )

                    if patient_fio != "не найдено" and policy_number != "не найдено":
                        print(
                            f"Из RTF '{filename}' извлечено: ФИО='{patient_fio}', Полис='{policy_number}'"
                        )
                        patient_obj = {
                            "patient_name": patient_fio,
                            "insurance_policy_number": policy_number,
                        }
                        if date_from:
                            patient_obj["date_from"] = date_from
                        if date_to:
                            patient_obj["date_to"] = date_to
                        patients_data.append(patient_obj)

                except Exception as e:
                    print(f"Ошибка при обработке RTF-файла '{filename}': {e}")

    finalize_and_add_patients_json(form_data, patients_data)

    return form_data
