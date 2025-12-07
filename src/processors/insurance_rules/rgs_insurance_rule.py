import io
import re

import pandas as pd
from aiohttp import FormData
from bs4 import BeautifulSoup

from src.processors.utils.form_data_finalize import \
    finalize_and_add_patients_json
from src.processors.utils.formatters import clean_message_text
from src.processors.utils.pdf_parser import extract_text_from_pdf
from src.processors.utils.universal_search_table_func import \
    universal_search_table_func
from src.processors.utils.zip_extractors import extract_files_from_zip


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
            if not isinstance(file_bytes, (bytes, bytearray)):
                file_bytes = bytes(file_bytes)
            form_data.add_field(
                "files",
                file_bytes,
                filename=filename,
            )

            lowered_name = filename.lower()

            if lowered_name.endswith(".pdf"):
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

            if lowered_name.endswith((".xls", ".xlsx")):
                try:
                    df = pd.read_excel(io.BytesIO(file_bytes), header=None)
                    data = universal_search_table_func(
                        df, fio_syn=["ФИО"], polis_syn=["Полис"]
                    )
                    patients_data.extend(data)
                except Exception as e:
                    print(f"Произошла ошибка при обработке файла {filename}: {e}")

            if lowered_name.endswith(".zip"):
                extracted_files = extract_files_from_zip(
                    file_bytes,
                    allowed_extensions=(".xls", ".xlsx"),
                    password="rgs",
                )
                for inner_name, inner_bytes in extracted_files:
                    try:
                        df = pd.read_excel(io.BytesIO(inner_bytes), header=None)
                        data = universal_search_table_func(
                            df, fio_syn=["ФИО"], polis_syn=["Полис"]
                        )
                        patients_data.extend(data)
                    except Exception as e:
                        print(
                            f"Произошла ошибка при обработке вложенного файла {inner_name}: {e}"
                        )
                if not extracted_files:
                    print(f"Не удалось извлечь таблицу из ZIP '{filename}'")
    finalize_and_add_patients_json(form_data, patients_data)

    return form_data
