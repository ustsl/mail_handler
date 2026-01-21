import io
import re

import pandas as pd
from aiohttp import FormData
from bs4 import BeautifulSoup

from src.processors.utils.form_data_finalize import finalize_and_add_patients_json
from src.processors.utils.formatters import clean_message_text
from src.processors.utils.pdf_parser import extract_text_from_pdf
from src.processors.utils.universal_search_table_func import \
    universal_search_table_func_v2
from src.processors.utils.zip_extractors import extract_files_from_zip
from src.processors.utils.date_helpers import (
    extract_date_range,
    normalize_date,
)
def _extract_policy_dates(text: str) -> tuple[str | None, str | None]:
    count_from, count_to = extract_date_range(
        text,
        r"Гарантийное письмо(?:\s+действительно)?:\s*с\s+(\d{2}\.\d{2}\.\d{4})\s+по\s+(\d{2}\.\d{2}\.\d{4})",
        flags=re.IGNORECASE,
    )

    if not count_to:
        to_match = re.search(
            r"Действует до\s+([\d\.]+\s*[А-Яа-я]+?\s*\d{4})",
            text,
            flags=re.IGNORECASE,
        )
        if to_match:
            count_to = normalize_date(to_match.group(1))

    return count_from, count_to


def sber_insurance_rule(
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
                except Exception as e:
                    print(f"Ошибка при обработке PDF-файла '{filename}': {e}")
                    continue

                date_from, date_to = _extract_policy_dates(pdf_text)

                fio_pattern = r"ФИО:\s*([А-ЯЁ][а-яё]+(?:\s+[А-ЯЁ][а-яё]+){1,2})"
                fio_match = re.search(fio_pattern, pdf_text)
                policy_pattern = r"Номер\s+ID\s*\(полис\):\s*(\S+)"
                policy_match = re.search(policy_pattern, pdf_text)

                if fio_match and policy_match:
                    patient_fio = fio_match.group(1).strip()
                    policy_number = policy_match.group(1).strip()
                    patient_obj = {
                        "patient_name": patient_fio,
                        "insurance_policy_number": policy_number,
                    }
                    if date_from:
                        patient_obj["date_from"] = date_from
                    if date_to:
                        patient_obj["date_to"] = date_to
                    print(
                        f"Из PDF '{filename}' извлечено: ФИО='{patient_fio}', Полис='{policy_number}'"
                    )
                    patients_data.append(patient_obj)
                else:
                    try:
                        fallback_pdf_text = extract_text_from_pdf(file_bytes)
                        fio_pattern = r"([А-ЯЁ]{2,}\s[А-ЯЁ]{2,}\s[А-ЯЁ]{2,})"
                        fio_match = re.search(fio_pattern, fallback_pdf_text)
                        policy_pattern = r"Номер полиса\s*(\S+)"
                        policy_match = re.search(policy_pattern, fallback_pdf_text)
                        if fio_match and policy_match:
                            patient_fio = fio_match.group(1).strip()
                            policy_number = policy_match.group(1).strip()
                            patient_obj = {
                                "patient_name": patient_fio,
                                "insurance_policy_number": policy_number,
                            }
                            if date_to:
                                patient_obj["date_to"] = date_to
                            print(
                                f"Из PDF '{filename}' извлечено: ФИО='{patient_fio}', Полис='{policy_number}'"
                            )
                            patients_data.append(patient_obj)
                        else:
                            print(f"В файле '{filename}' не удалось найти ФИО или полис")
                    except Exception as exc:
                        print(f"Ошибка при обработке PDF-файла '{filename}': {exc}")

    finalize_and_add_patients_json(form_data, patients_data)

    return form_data


def sber_ins_insurance_rule(
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

                fio_pattern = (
                    r"Застрахованный:\s*([А-ЯЁ][а-яё]+(?:\s+[А-ЯЁ][а-яё]+){1,2})"
                )
                fio_match = re.search(fio_pattern, pdf_text)
                policy_pattern = r"Номер договора:\s*([A-ZА-Я0-9\-]+)"
                policy_match = re.search(policy_pattern, pdf_text)

                if fio_match and policy_match:
                    patient_fio = fio_match.group(1).strip()
                    policy_number = policy_match.group(1).strip()
                    print(
                        f"Из PDF '{filename}' извлечено: ФИО='{patient_fio}', Полис='{policy_number}'"
                    )
                    patients_data.append(
                        {
                            "patient_name": patient_fio,
                            "insurance_policy_number": policy_number,
                        }
                    )
                else:
                    print(f"В файле '{filename}' не удалось найти ФИО или полис")

            except Exception as e:
                print(f"Ошибка при обработке PDF-файла '{filename}': {e}")
                try:
                    pdf_text = extract_text_from_pdf(file_bytes)

                    fio_pattern = r"([А-ЯЁ]{2,}\s[А-ЯЁ]{2,}\s[А-ЯЁ]{2,})"
                    fio_match = re.search(fio_pattern, pdf_text)

                    policy_pattern = r"Номер полиса\s*(\S+)"
                    policy_match = re.search(policy_pattern, pdf_text)

                    if fio_match and policy_match:
                        patient_fio = fio_match.group(1).strip()
                        policy_number = policy_match.group(1).strip()
                        print(
                            f"Из PDF '{filename}' извлечено: ФИО='{patient_fio}', Полис='{policy_number}'"
                        )
                        patients_data.append(
                            {
                                "patient_name": patient_fio,
                                "insurance_policy_number": policy_number,
                            }
                        )

                except Exception as e:
                    print(f"Ошибка при обработке PDF-файла '{filename}': {e}")

    finalize_and_add_patients_json(form_data, patients_data)

    return form_data


def sber_digital_assistant_insurance_rule(
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
        def _to_bytes(data: bytes | bytearray | list[int]) -> bytes:
            return data if isinstance(data, (bytes, bytearray)) else bytes(data)

        for filename, file_bytes in attachments:
            safe_file_bytes = _to_bytes(file_bytes)
            form_data.add_field("files", safe_file_bytes, filename=filename)

            lowered_name = filename.lower()

            def _process_excel_bytes(data: bytes, source_name: str) -> None:
                nonlocal patients_data
                try:
                    df = pd.read_excel(io.BytesIO(_to_bytes(data)), header=None)
                    patients = universal_search_table_func_v2(
                        df,
                        name_parts_headers=["Фамилия", "Имя", "Отчество"],
                        polis_syn=["№ полиса (ID)"],
                    )
                    patients_data.extend(patients)
                except Exception as e:
                    print(
                        f"Ошибка при обработке Excel-файла '{source_name}' из письма digital.assistant: {e}"
                    )

            if lowered_name.endswith(".xlsx"):
                _process_excel_bytes(safe_file_bytes, filename)
            elif lowered_name.endswith(".zip"):
                extracted_files = extract_files_from_zip(
                    safe_file_bytes,
                    allowed_extensions=(".xls", ".xlsx"),
                    pin_length=4,
                )
                for inner_name, inner_bytes in extracted_files:
                    _process_excel_bytes(inner_bytes, inner_name)
                if not extracted_files:
                    print(
                        f"Не удалось извлечь Excel из ZIP '{filename}' для digital.assistant@sberins.ru"
                    )

    finalize_and_add_patients_json(form_data, patients_data)

    return form_data
