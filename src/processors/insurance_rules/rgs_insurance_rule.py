import re
from aiohttp import FormData
from bs4 import BeautifulSoup

from src.processors.utils.form_data_finalize import finalize_and_add_patients_json
from src.processors.utils.pdf_parser import extract_text_from_pdf
from src.processors.utils.formatters import clean_message_text


def rgs_insurance_rule(
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

            if filename.lower().endswith(".pdf"):
                try:
                    pdf_text = extract_text_from_pdf(file_bytes)

                    if pdf_text:
                        pdf_text = pdf_text.replace("\xa0", " ")

                    patient_fio = ""
                    policy_number = ""

                    fio_pattern = r"Застрахованному лицу:\s*([А-ЯЁ\s]+?),"
                    fio_match = re.search(fio_pattern, pdf_text)
                    if fio_match:
                        patient_fio = fio_match.group(1).replace("\n", " ").strip()

                    policy_pattern = r"Полис([\s\S]{1,100}?)Страхователь:"
                    policy_match = re.search(policy_pattern, pdf_text, re.IGNORECASE)

                    if policy_match:
                        raw_policy_block = policy_match.group(1)
                        policy_number = re.sub(r"\s+", "", raw_policy_block)
                    patients_data.append(
                        {
                            "patient_name": patient_fio,
                            "insurance_policy_number": policy_number,
                        }
                    )
                    print(
                        f"Извлечено из PDF: ФИО='{patient_fio}', Полис='{policy_number}'"
                    )

                except Exception as e:
                    print(f"Ошибка при обработке PDF-файла '{filename}': {e}")

    finalize_and_add_patients_json(form_data, patients_data)

    return form_data
