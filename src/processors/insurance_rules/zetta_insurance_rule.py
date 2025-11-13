import re

from aiohttp import FormData
from bs4 import BeautifulSoup

from src.processors.utils.form_data_finalize import \
    finalize_and_add_patients_json
from src.processors.utils.formatters import clean_message_text


def zetta_insurance_rule(
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

    if subject:
        try:
            parts = [p.strip() for p in subject.split(",")]

            if len(parts) >= 5:
                patient_name = parts[3]
                policy_part = parts[4]

                policy_match = re.search(r"^\d+", policy_part)
                if policy_match:
                    policy_number = policy_match.group(0)

                    patients_data.append(
                        {
                            "patient_name": patient_name,
                            "insurance_policy_number": policy_number,
                        }
                    )

        except Exception as e:
            print(f"Не удалось извлечь данные из темы письма '{subject}': {e}")

    if attachments:
        for filename, file_bytes in attachments:
            form_data.add_field(
                "files",
                file_bytes,
                filename=filename,
            )

    finalize_and_add_patients_json(form_data, patients_data)

    return form_data
