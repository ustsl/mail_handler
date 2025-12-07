import io
import re

import pandas as pd
from aiohttp import FormData
from bs4 import BeautifulSoup

from src.processors.utils.form_data_finalize import finalize_and_add_patients_json
from src.processors.utils.formatters import clean_message_text
from src.processors.utils.pdf_parser import extract_text_from_pdf
from src.processors.utils.universal_search_table_func import universal_search_table_func
from src.processors.utils.zip_extractors import extract_files_from_zip


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
                text_spaced = re.sub(r"\s+", " ", pdf_text).strip()
                text_glued = re.sub(r"\s+", "", pdf_text)
                patient_fio = None
                policy_number = None
                policy_patterns = [
                    r"(?:№\s*полис[аa]\s*[:\-]?\s*)([0-9A-Z][0-9A-Z\-\/]+)",
                    r"(?:Номер\s*(?:ID|полиса)\s*[:\-]?\s*)([0-9A-Z\-\/]+)",
                    r"\b\d{2,}-\d{2}-\d{5,}-\d{2}\/\d{2,}\b",
                ]
                for pat in policy_patterns:
                    m = re.search(pat, text_spaced, flags=re.IGNORECASE)
                    if not m:
                        m = re.search(pat, text_glued, flags=re.IGNORECASE)
                    if m:
                        policy_number = m.group(1) if m.lastindex else m.group(0)
                        policy_number = policy_number.strip()
                        break
                fio_patterns = [
                    r"Ф\.?\s*И\.?\s*О\.?.{0,40}?([А-ЯЁ][а-яё]+(?:\s+[А-ЯЁ][а-яё]+){1,2})",
                    r"\b([А-ЯЁ][а-яё]+ [А-ЯЁ][а-яё]+(?: [А-ЯЁ][а-яё]+)?)\b",
                ]
                for pat in fio_patterns:
                    m = re.search(pat, text_spaced)
                    if not m:
                        m = re.search(r"№полисаФ\.?И\.?О\.?(.{0,60})", text_glued)
                        if m:
                            frag = m.group(1)
                            frag = re.sub(r"([А-ЯЁ][а-яё]+)", r" \1", frag)
                            m2 = re.search(
                                r"\b([А-ЯЁ][а-яё]+ [А-ЯЁ][а-яё]+(?: [А-ЯЁ][а-яё]+)?)\b",
                                frag,
                            )
                            if m2:
                                patient_fio = m2.group(1).strip()
                                break
                    if m:
                        patient_fio = m.group(1).strip()
                        break

                if patient_fio and policy_number:
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
