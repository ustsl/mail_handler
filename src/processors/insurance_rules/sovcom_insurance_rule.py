import io
import re
from datetime import datetime

import pandas as pd
from aiohttp import FormData
from bs4 import BeautifulSoup

from src.processors.utils.form_data_finalize import finalize_and_add_patients_json
from src.processors.utils.formatters import clean_message_text
from src.processors.utils.pdf_parser import extract_text_from_pdf
from src.processors.utils.universal_search_table_func import universal_search_table_func
from src.processors.utils.zip_extractors import extract_files_from_zip


def _normalize_pdf_text(text: str) -> str:
    text = text.replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"([А-Яа-яЁё])(?=\d)", r"\1 ", text)
    text = re.sub(r"(\d)(?=[А-Яа-яЁё])", r"\1 ", text)
    text = re.sub(
        r"(\d{2}\.\d{2}\.\d{2,4})(?=\d{2}\.\d{2}\.\d{2,4})", r"\1 ", text
    )
    return text


def _format_date(value: str) -> str:
    value = value.strip()
    for fmt in ("%d.%m.%Y", "%d.%m.%y"):
        try:
            return datetime.strptime(value, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return value


def sovcom_insurance_rule(
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
                    if not pdf_text:
                        print(f"В файле '{filename}' не удалось извлечь текст")
                        continue

                    text_spaced = _normalize_pdf_text(pdf_text)

                    patient_fio = None
                    policy_number = None
                    date_from = None
                    date_to = None

                    policy_patterns = [
                        r"(?:№\s*полис[аa]?\s*[:\-]?\s*)([0-9A-Z][0-9A-Z\-\/]+)",
                        r"(?:Номер\s*(?:ID|полиса)\s*[:\-]?\s*)([0-9A-Z\-\/]+)",
                        r"\b\d{2,}-\d{2}-\d{5,}-\d{2}\/\d{2,}\b",
                    ]
                    for pat in policy_patterns:
                        m = re.search(pat, text_spaced, flags=re.IGNORECASE)
                        if m:
                            policy_number = m.group(1) if m.lastindex else m.group(0)
                            policy_number = policy_number.strip()
                            break

                    fio_word = r"[А-ЯЁ][А-ЯЁа-яё]+"
                    fio_patterns = [
                        rf"Ф\.?\s*И\.?\s*О\.?.{{0,40}}?({fio_word}(?:\s+{fio_word}){{1,2}})",
                        rf"№\s*полис[аa]?\s*Ф\.?\s*И\.?\s*О\.?.{{0,60}}?({fio_word}(?:\s+{fio_word}){{1,2}})",
                    ]
                    for pat in fio_patterns:
                        m = re.search(pat, text_spaced)
                        if m:
                            patient_fio = m.group(1).strip()
                            break

                    date_range_pattern = (
                        r"(?:С|C)\s*[:\-]?\s*(\d{2}\.\d{2}\.\d{2,4})"
                        r"\s*(?:ПО|ДО)\s*[:\-]?\s*(\d{2}\.\d{2}\.\d{2,4})"
                    )
                    date_match = re.search(date_range_pattern, text_spaced, flags=re.IGNORECASE)
                    if date_match:
                        date_from = _format_date(date_match.group(1))
                        date_to = _format_date(date_match.group(2))

                    if patient_fio and policy_number:
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
                        print(f"В файле '{filename}' не удалось найти ФИО или полис")
                except Exception as e:
                    print(f"Ошибка при обработке PDF-файла '{filename}': {e}")

            if filename.lower().endswith(".zip"):
                print("начинаем зип")
                extracted_files = extract_files_from_zip(
                    file_bytes, allowed_extensions=(".xls", ".xlsx"), password="rgs"
                )
                for inner_name, inner_bytes in extracted_files:
                    try:
                        df = pd.read_excel(io.BytesIO(inner_bytes), header=None)
                        print(df)
                        print("датасет")
                        data = universal_search_table_func(
                            df, fio_syn=["ФИО"], polis_syn=["Полис №"]
                        )

                        print(data)
                        patients_data.extend(data)
                    except Exception as e:
                        print(
                            f"Произошла ошибка при обработке вложенного файла {inner_name}: {e}"
                        )
                if not extracted_files:
                    print(f"Не удалось извлечь таблицу из ZIP '{filename}'")
    finalize_and_add_patients_json(form_data, patients_data)

    return form_data
