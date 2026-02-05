import io
import re

import pandas as pd
import pypdf
from aiohttp import FormData
from bs4 import BeautifulSoup

from src.processors.utils.form_data_finalize import \
    finalize_and_add_patients_json
from src.processors.utils.formatters import clean_message_text
from src.processors.utils.date_helpers import extract_date_range
from src.processors.utils.pdf_parser import extract_text_from_pdf


def _extract_luchi_dates(text: str) -> tuple[str | None, str | None]:
    date_from, date_to = extract_date_range(
        text,
        r"Срок действия полиса:\s*[сc]\s*(\d{2}\.\d{2}\.\d{2,4})\s*по\s*(\d{2}\.\d{2}\.\d{2,4})",
        flags=re.IGNORECASE,
    )
    if not date_from or not date_to:
        fallback = extract_date_range(
            text,
            r"Гарантийное письмо\s+действительно\s*[сc]\s*(\d{2}\.\d{2}\.\d{2,4})\s*по\s*(\d{2}\.\d{2}\.\d{2,4})",
            flags=re.IGNORECASE,
        )
        date_from = date_from or fallback[0]
        date_to = date_to or fallback[1]
    if not date_from or not date_to:
        generic = extract_date_range(
            text,
            r"\b[сc]\s*(\d{2}\.\d{2}\.\d{2,4})\s*по\s*(\d{2}\.\d{2}\.\d{2,4})",
            flags=re.IGNORECASE,
        )
        date_from = date_from or generic[0]
        date_to = date_to or generic[1]
    return date_from, date_to


def luchi_insurance_rule(
    content: str | None,
    subject: str,
    sender: str,
    attachments: list[tuple[str, bytes]] | None,
) -> FormData:
    """
    Обрабатывает гарантийные письма от «Лучи Здоровье».
    Извлекает данные из PDF или Excel файлов.
    """
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

                    if pdf_text:
                        patient_fio = ""
                        policy_number = ""
                        date_from = None
                        date_to = None

                        fio_pattern = r"Пациент:\s*(.*?)\n"
                        fio_match = re.search(fio_pattern, pdf_text)
                        if fio_match:
                            patient_fio = fio_match.group(1).strip()

                        policy_pattern = r"Номер полиса:\s*([^\n]+)"
                        policy_match = re.search(policy_pattern, pdf_text)
                        if policy_match:
                            policy_number = re.sub(
                                r"\s+", " ", policy_match.group(1)
                            ).strip()

                        date_from, date_to = _extract_luchi_dates(pdf_text)

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
                            print(
                                f"В PDF '{filename}' не удалось найти ФИО и/или Полис."
                            )

                except Exception as e:
                    print(f"Ошибка при обработке PDF-файла '{filename}': {e}")

            elif filename.lower().endswith((".xls", ".xlsx")):
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
                                policy_str = str(policy_num).strip()
                                print(
                                    f"Из Excel '{filename}' извлечено: ФИО='{full_name}', Полис='{policy_str}'"
                                )
                                patients_data.append(
                                    {
                                        "patient_name": full_name,
                                        "insurance_policy_number": policy_str,
                                    }
                                )
                except Exception as e:
                    print(f"Ошибка при обработке Excel-файла '{filename}': {e}")

    finalize_and_add_patients_json(form_data, patients_data)

    return form_data
