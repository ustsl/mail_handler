import io
import re

import pandas as pd
from aiohttp import FormData
from bs4 import BeautifulSoup

from src.processors.utils.date_helpers import extract_date_range
from src.processors.utils.form_data_finalize import (
    finalize_and_add_patients_json,
)
from src.processors.utils.formatters import clean_message_text
from src.processors.utils.pdf_parser import extract_text_from_pdf


def _extract_ingos_pdf_patients(pdf_text: str) -> list[tuple[str, str]]:
    table_match = re.search(
        r"ФИО\s+Дата\s*[\r\n]+\s*рождения\s+№\s*Полиса\s+Страхователь\s+№\s*Договора\s*ДМС\s*([\s\S]+?)(?:\n\s*Оплата|\n\s*Жалобы:|\Z)",
        pdf_text,
        re.IGNORECASE,
    )
    search_area = table_match.group(1) if table_match else pdf_text

    row_pattern = re.compile(
        r"([А-ЯЁ][А-ЯЁ\-]+(?:\s+[А-ЯЁ][А-ЯЁ\-]+){1,2})\s+(\d{2}\.\d{2}\.\d{4})\s+([A-Za-zА-Яа-яЁё0-9][A-Za-zА-Яа-яЁё0-9/.-]*)",
        re.MULTILINE,
    )

    patients: list[tuple[str, str]] = []
    for match in row_pattern.finditer(search_area):
        patient_name = " ".join(match.group(1).split()).strip()
        policy_number = match.group(3).strip()
        if patient_name and policy_number:
            patients.append((patient_name, policy_number))

    return patients


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
                        date_from = None
                        date_to = None
                        date_from, date_to = extract_date_range(
                            pdf_text,
                            r"Срок\s+действия(?:\s+гарантийного\s+письма)?\s+с\s+(\d{2}\.\d{2}\.\d{4})\s+по\s+(\d{2}\.\d{2}\.\d{4})",
                            re.IGNORECASE,
                        )
                        if not date_from or not date_to:
                            fallback_range = extract_date_range(
                                pdf_text,
                                r"с\s+(\d{2}\.\d{2}\.\d{4})\s+(?:по|до)\s+(\d{2}\.\d{2}\.\d{4})",
                                flags=re.IGNORECASE,
                            )
                            date_from = date_from or fallback_range[0]
                            date_to = date_to or fallback_range[1]

                        parsed_patients = _extract_ingos_pdf_patients(pdf_text)
                        for patient_fio, policy_number in parsed_patients:
                            patient_obj = {
                                "patient_name": patient_fio,
                                "insurance_policy_number": policy_number,
                            }
                            if date_from:
                                patient_obj["date_from"] = date_from
                            if date_to:
                                patient_obj["date_to"] = date_to
                            patients_data.append(patient_obj)
                        if parsed_patients:
                            continue

                        fio_match = re.search(
                            r"ФИО:\s*([А-ЯЁ][а-яё]+(?:\s+[А-ЯЁ][а-яё]+){1,2})",
                            pdf_text,
                        )
                        policy_match = re.search(
                            r"(?:№\s*Полиса|Полис(?:\s*№)?)\s*[:\-]?\s*([A-Za-zА-Яа-яЁё0-9/.-]+)",
                            pdf_text,
                            re.IGNORECASE,
                        )
                        if fio_match and policy_match:
                            patient_obj = {
                                "patient_name": fio_match.group(1).strip(),
                                "insurance_policy_number": policy_match.group(1).strip(),
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
