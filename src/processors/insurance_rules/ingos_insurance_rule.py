import re
import io
from aiohttp import FormData
from bs4 import BeautifulSoup
import pypdf


from src.processors.utils.formatters import clean_message_text


def ingos_insurance_rule(
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

    if attachments:
        for filename, file_bytes in attachments:
            form_data.add_field(
                "files",
                file_bytes,
                filename=filename,
            )

            if filename.lower().endswith(".pdf"):
                try:
                    pdf_file = io.BytesIO(file_bytes)
                    reader = pypdf.PdfReader(pdf_file)
                    pdf_text = ""
                    for page in reader.pages:
                        pdf_text += page.extract_text() or ""

                    patient_fio = None
                    policy_number = None

                    fio_pattern = (
                        r"ФИО Дата \nрождения[^\n]*\n(.*?) \d{2}\.\d{2}\.\d{4}"
                    )
                    fio_match = re.search(fio_pattern, pdf_text, re.DOTALL)

                    policy_pattern = (
                        r"ФИО Дата \nрождения.*?\d{2}\.\d{2}\.\d{4}\s+(\S+)"
                    )
                    policy_match = re.search(policy_pattern, pdf_text, re.DOTALL)

                    if fio_match:
                        raw_fio = fio_match.group(1)
                        patient_fio = re.sub(r"\s+", " ", raw_fio).strip()

                    if policy_match:
                        policy_number = policy_match.group(1).strip()

                    if patient_fio:
                        print(f"ФИО пациента: {patient_fio}")
                        form_data.add_field("patient_name", patient_fio)

                    if policy_number:
                        print(f"Номер полиса пациента: {policy_number}")
                        form_data.add_field("insurance_policy_number", policy_number)

                except Exception as e:
                    print(f"Ошибка при обработке PDF-файла '{filename}': {e}")

    return form_data
