import io
import re
from datetime import datetime

import pandas as pd
from aiohttp import FormData
from bs4 import BeautifulSoup

from src.processors.utils.form_data_finalize import (
    finalize_and_add_patients_json,
)
from src.processors.utils.formatters import clean_message_text
from src.processors.utils.pdf_parser import extract_text_from_pdf


def _normalize_date(value: str) -> str | None:
    """Convert Russian dd.mm.yyyy dates to ISO-8601 (YYYY-MM-DD)."""

    text = value.strip()
    for fmt in ("%d.%m.%Y", "%d.%m.%y"):
        try:
            return datetime.strptime(text, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return None


def fix_encoding(text: str) -> str:
    """
    Автоматически определяет и исправляет текст, который был в кодировке KOI8-R,
    но ошибочно прочитан как CP1251. Если текст не похож на искаженный,
    он возвращается без изменений.
    """
    if not text:
        return ""

    try:
        re_encoded_text = text.encode("cp1251").decode("koi8-r")
        cyrillic_chars_re = re.compile(r"[а-яА-ЯёЁ]")

        original_cyrillic_count = len(cyrillic_chars_re.findall(text))
        re_encoded_cyrillic_count = len(cyrillic_chars_re.findall(re_encoded_text))

        if re_encoded_cyrillic_count > original_cyrillic_count + 5:
            return re_encoded_text
        else:
            return text

    except (UnicodeEncodeError, UnicodeDecodeError):
        return text


def ingosstrah_insurance_rule(
    content: str | None,
    subject: str,
    sender: str,
    attachments: list[tuple[str, bytes]] | None,
) -> FormData:
    form_data = FormData()

    corrected_subject = fix_encoding(subject)

    cleaned_text = ""
    if content:
        soup = BeautifulSoup(content, "html.parser")
        raw_text = soup.get_text(separator="\n")
        corrected_text = fix_encoding(raw_text)
        cleaned_text = clean_message_text(corrected_text)
    if subject:
        subject = fix_encoding(subject)

    form_data.add_field("insurance_email_sender", sender)
    form_data.add_field("subject", corrected_subject)
    form_data.add_field("original_message", cleaned_text)

    patients_data = []

    if attachments:
        for filename, file_bytes in attachments:
            form_data.add_field("files", file_bytes, filename=filename)

            if filename.lower().endswith(".pdf"):
                try:
                    pdf_text = extract_text_from_pdf(file_bytes)

                    if pdf_text:

                        patient_fio = None
                        policy_number = None
                        date_from = None
                        date_to = None
                        guaranty_match = re.search(
                            r"Срок\s+действия(?:\s+гарантийного\s+письма)?\s+с\s+(\d{2}\.\d{2}\.\d{4})\s+по\s+(\d{2}\.\d{2}\.\d{4})",
                            pdf_text,
                            re.IGNORECASE,
                        )
                        if guaranty_match:
                            date_from = _normalize_date(guaranty_match.group(1))
                            date_to = _normalize_date(guaranty_match.group(2))

                        fio_pattern = (
                            r"№\s+Договора\s+ДМС\s*\n([\s\S]+?)\s*\d{2}\.\d{2}\.\d{4}"
                        )
                        fio_match = re.search(fio_pattern, pdf_text)

                        if fio_match:
                            patient_fio = fio_match.group(1).replace("\n", " ").strip()

                        end_marker = "Оплата будет"
                        end_marker_pos = pdf_text.find(end_marker)

                        if end_marker_pos != -1:
                            search_area = pdf_text[:end_marker_pos]
                            policy_matches = re.findall(r"\b(\d+-\d+)\b", search_area)
                            if policy_matches:
                                policy_number = policy_matches[-1]

                        if patient_fio and policy_number:
                            patient_obj = {
                                "patient_name": patient_fio,
                                "insurance_policy_number": policy_number,
                            }
                            if date_from:
                                patient_obj["date_from"] = date_from
                            if date_to:
                                patient_obj["date_to"] = date_to
                            patients_data.append(patient_obj)
                except Exception as e:
                    print(f"Ошибка при обработке PDF-файла '{filename}': {e}")

            if filename.lower().endswith((".xls", ".xlsx")):
                try:
                    df = pd.read_excel(io.BytesIO(file_bytes), header=None)
                    header_row_index = -1
                    (
                        last_name_col_index,
                        first_name_col_index,
                        patronymic_col_index,
                        policy_num_col_index,
                    ) = (-1, -1, -1, -1)
                    required_headers = {"Фамилия", "Имя", "Отчество", "№ полиса"}

                    for i, row in df.iterrows():
                        row_values = {str(v).strip() for v in row.values if pd.notna(v)}
                        if required_headers.issubset(row_values):
                            header_row_index = i
                            header_list = [str(v).strip() for v in list(df.iloc[i])]
                            last_name_col_index = header_list.index("Фамилия")
                            first_name_col_index = header_list.index("Имя")
                            patronymic_col_index = header_list.index("Отчество")
                            policy_num_col_index = header_list.index("№ полиса")
                            break

                    if header_row_index != -1:
                        for i in range(header_row_index + 1, len(df)):
                            data_row = df.iloc[i]
                            first_cell_val = data_row.iloc[0]
                            if (
                                pd.isna(first_cell_val)
                                or not str(first_cell_val).strip().isdigit()
                            ):
                                break
                            last_name = data_row.iloc[last_name_col_index]
                            first_name = data_row.iloc[first_name_col_index]
                            patronymic = data_row.iloc[patronymic_col_index]
                            policy_num = data_row.iloc[policy_num_col_index]
                            if (
                                pd.notna(last_name)
                                and pd.notna(first_name)
                                and pd.notna(patronymic)
                                and pd.notna(policy_num)
                            ):
                                full_name = f"{str(last_name).strip()} {str(first_name).strip()} {str(patronymic).strip()}"
                                patients_data.append(
                                    {
                                        "patient_name": full_name,
                                        "insurance_policy_number": str(
                                            policy_num
                                        ).strip(),
                                    }
                                )
                except Exception as e:
                    print(f"Произошла ошибка при обработке файла {filename}: {e}")

    finalize_and_add_patients_json(form_data, patients_data)

    return form_data
