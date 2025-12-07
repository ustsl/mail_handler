import re

from aiohttp import FormData
from bs4 import BeautifulSoup

from src.processors.utils.form_data_finalize import \
    finalize_and_add_patients_json
from src.processors.utils.formatters import clean_message_text
from src.processors.utils.pdf_parser import extract_text_from_pdf
from src.processors.utils.zip_extractors import extract_files_from_zip

ZETTA_ZIP_PASSWORD = ",:nB-7mFN5"


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
            if not isinstance(file_bytes, (bytes, bytearray)):
                file_bytes = bytes(file_bytes)
            form_data.add_field(
                "files",
                file_bytes,
                filename=filename,
            )

    finalize_and_add_patients_json(form_data, patients_data)

    return form_data


def _extract_patient_from_pdf(pdf_bytes: bytes) -> dict[str, str] | None:
    pdf_text = extract_text_from_pdf(pdf_bytes)
    if not pdf_text:
        return None

    pdf_text = pdf_text.replace("\xa0", " ")
    clean_text = " ".join(pdf_text.split())

    fio_pattern = r"\d+\.\s+([А-ЯЁ\s]+),"
    match_fio = re.search(fio_pattern, clean_text)
    fio_result = "Не найдено"
    if match_fio:
        fio_result = match_fio.group(1).strip()

    contract_pattern = r"([А-Я]{4}-\d+/\d+)"
    match_contract = re.search(contract_pattern, clean_text)
    contract_result = "Не найдено"
    if match_contract:
        contract_result = match_contract.group(1)

    if fio_result == "Не найдено" and contract_result == "Не найдено":
        return None

    return {
        "patient_name": fio_result,
        "insurance_policy_number": contract_result,
    }


def zetta_pulse_insurance_rule(
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

    patients_data: list[dict[str, str]] = []

    if attachments:
        for filename, file_bytes in attachments:
            if not isinstance(file_bytes, (bytes, bytearray)):
                file_bytes = bytes(file_bytes)
            form_data.add_field(
                "files",
                file_bytes,
                filename=filename,
            )

            lowered_name = filename.lower()
            patient_info = None

            if lowered_name.endswith(".pdf"):
                try:
                    patient_info = _extract_patient_from_pdf(file_bytes)
                except Exception as e:
                    print(f"Ошибка при обработке PDF-файла '{filename}': {e}")
            elif lowered_name.endswith(".zip"):
                try:
                    extracted_files = extract_files_from_zip(
                        file_bytes,
                        allowed_extensions=(".pdf",),
                        password=ZETTA_ZIP_PASSWORD,
                    )
                    for inner_name, inner_bytes in extracted_files:
                        patient_info = _extract_patient_from_pdf(inner_bytes)
                        if patient_info:
                            patients_data.append(patient_info)
                        else:
                            print(
                                f"Не удалось извлечь данные из PDF внутри архива '{inner_name}'."
                            )
                    if not extracted_files:
                        print(
                            f"Не найден PDF внутри ZIP '{filename}', обработка пропущена."
                        )
                except Exception as e:
                    print(f"Ошибка при обработке ZIP-файла '{filename}': {e}")

            if patient_info:
                patients_data.append(patient_info)

    finalize_and_add_patients_json(form_data, patients_data)

    return form_data
