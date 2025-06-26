import re
import io
from aiohttp import FormData
from bs4 import BeautifulSoup
import pypdf


from src.processors.utils.formatters import clean_message_text


def sogaz_insurance_rule(
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

                    patient_block_match = re.search(
                        r"Застрахованный(.*?)Гарантируем", pdf_text, re.DOTALL
                    )

                    if patient_block_match:
                        patient_block_text = patient_block_match.group(1)

                        surname_match = re.search(r"^\s*(\w+)", patient_block_text)
                        name_match = re.search(r"(\w+).*?\n\s*имя", patient_block_text)
                        patronymic_match = re.search(
                            r"(\w+)\s*\n\s*отчество", patient_block_text
                        )

                        if surname_match and name_match and patronymic_match:
                            patient_fio = f"{surname_match.group(1)} {name_match.group(1)} {patronymic_match.group(1)}"

                        policy_pattern = r"([A-Z\d\s/.-]+?)\s+с\s+\d{2}\.\d{2}\.\d{4}"
                        policy_match = re.search(policy_pattern, patient_block_text)
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
