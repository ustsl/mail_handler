import re
from aiohttp import FormData
from bs4 import BeautifulSoup
from datetime import datetime
from src.processors.utils.pdf_parser import extract_text_from_pdf
from src.processors.utils.form_data_finalize import finalize_and_add_patients_json
from src.processors.utils.formatters import clean_message_text


def energogarant_insurance_rule(
    content: str | None,
    subject: str,
    sender: str,
    attachments: list[tuple[str, bytes]] | None,
) -> FormData:
    """
    Правило для обработки писем и гарантийных писем от СК "Энергогарант".
    Извлекает данные из PDF-вложений и форматирует даты.
    """
    form_data = FormData()

    # ... (код очистки HTML остается без изменений)
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
                    if not pdf_text:
                        continue
                    pdf_text = pdf_text.replace("\xa0", " ")

                    patient_fio = ""
                    policy_number = ""
                    issue_date = None
                    expiry_date = None

                    data_line_pattern = r"(\d{6}-\d{3}-\d{6}-\d{2})\s+([А-ЯЁ][а-яё]+\s[А-ЯЁ][а-яё]+\s[А-ЯЁ][а-яё]+)"

                    if data_match := re.search(data_line_pattern, pdf_text):
                        policy_number = data_match.group(1)
                        patient_fio = data_match.group(2)

                    issue_date_pattern = (
                        r"Дата выдачи направления:\s*(\d{2}\.\d{2}\.\d{4})"
                    )

                    if issue_date_match := re.search(issue_date_pattern, pdf_text):
                        original_issue_date = issue_date_match.group(1)
                        try:
                            issue_date = datetime.strptime(
                                original_issue_date, "%d.%m.%Y"
                            ).strftime("%Y-%m-%d")
                        except ValueError:
                            issue_date = original_issue_date

                    expiry_date_pattern = (
                        r"Срок действия направления до:\s*(\d{2}\.\d{2}\.\d{4})"
                    )
                    if expiry_date_match := re.search(expiry_date_pattern, pdf_text):
                        original_expiry_date = expiry_date_match.group(1)
                        try:
                            expiry_date = datetime.strptime(
                                original_expiry_date, "%d.%m.%Y"
                            ).strftime("%Y-%m-%d")
                        except ValueError:
                            expiry_date = original_expiry_date

                    if patient_fio or policy_number:
                        patient_obj = {
                            "patient_name": patient_fio,
                            "insurance_policy_number": policy_number,
                        }
                        if issue_date:
                            patient_obj["date_from"] = issue_date
                        if expiry_date:
                            patient_obj["date_to"] = expiry_date
                        patients_data.append(patient_obj)
                        print(patient_obj)

                except Exception as e:
                    print(f"❌ Ошибка при обработке PDF-файла '{filename}': {e}")

    finalize_and_add_patients_json(form_data, patients_data)

    return form_data
