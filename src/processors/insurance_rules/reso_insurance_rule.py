import re
from aiohttp import FormData
from bs4 import BeautifulSoup

from striprtf.striprtf import rtf_to_text
from src.processors.utils.form_data_finalize import finalize_and_add_patients_json
from src.processors.utils.formatters import clean_message_text


def reso_insurance_rule(
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

                    row_pattern = r"\d+\|([\d-]+/\d+)\|([А-ЯЁ\s]+?)\|"
                    found_rows = re.findall(row_pattern, plain_text)

                    print(
                        f"В RTF-файле '{filename}' найдено {len(found_rows)} записей пациентов."
                    )

                    for row in found_rows:
                        policy_number = row[0].strip()
                        patient_fio = row[1].strip()

                        patients_data.append(
                            {
                                "patient_name": patient_fio,
                                "insurance_policy_number": policy_number,
                            }
                        )

                except Exception as e:
                    print(f"Ошибка при обработке RTF-файла '{filename}': {e}")

    finalize_and_add_patients_json(form_data, patients_data)

    return form_data
