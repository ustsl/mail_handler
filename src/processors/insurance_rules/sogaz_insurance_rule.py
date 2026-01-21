import io

import re

import pandas as pd
from aiohttp import FormData
from bs4 import BeautifulSoup

from src.processors.utils.date_helpers import extract_date_range
from src.processors.utils.formatters import clean_message_text
from src.processors.utils.patient_chunker import finalize_and_chunk_patients
from src.processors.utils.pdf_parser import extract_text_from_pdf


def sogaz_insurance_rule(
    content: str | None,
    subject: str,
    sender: str,
    attachments: list[tuple[str, bytes]] | None,
) -> FormData | list[FormData]:
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
            form_data.add_field("files", file_bytes, filename=filename)
            if filename.lower().endswith(".pdf"):
                pdf_text = extract_text_from_pdf(file_bytes)
                if pdf_text:
                    patient_fio = ""
                    policy_number = ""
                    date_from = None
                    date_to = None
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
                    if not date_from or not date_to:
                        range_match = extract_date_range(
                            pdf_text,
                            r"Срок\s+действия(?:\s+гарантийного\s+письма)?\s*(?:[^\\n]+?)?\s*с\s+(\d{2}\.\d{2}\.\d{4})\s+(?:по|до)\s+(\d{2}\.\d{2}\.\d{4})",
                            flags=re.IGNORECASE,
                        )
                        date_from = date_from or range_match[0]
                        date_to = date_to or range_match[1]
                    if not date_from or not date_to:
                        fallback_match = extract_date_range(
                            pdf_text,
                            r"с\s+(\d{2}\.\d{2}\.\d{4})\s+(?:по|до)\s+(\d{2}\.\d{2}\.\d{4})",
                            flags=re.IGNORECASE,
                        )
                        date_from = date_from or fallback_match[0]
                        date_to = date_to or fallback_match[1]
                    patient_obj = {
                        "patient_name": str(patient_fio),
                        "insurance_policy_number": str(policy_number),
                    }
                    if date_from:
                        patient_obj["date_from"] = date_from
                    if date_to:
                        patient_obj["date_to"] = date_to
                    patients_data.append(patient_obj)

            if filename.lower().endswith((".xls", ".xlsx")):
                try:
                    df = pd.read_excel(io.BytesIO(file_bytes), header=None)

                    header_row_index = -1
                    last_name_col_index = -1
                    first_name_col_index = -1
                    patronymic_col_index = -1
                    policy_num_col_index = -1

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
                        print(
                            f"  > Заголовок найден в строке {header_row_index} файла '{filename}'. Начинаем сбор данных..."
                        )
                        empty_streak = 0
                        for i in range(header_row_index + 1, len(df)):
                            data_row = df.iloc[i]

                            last_name = data_row.iloc[last_name_col_index]
                            first_name = data_row.iloc[first_name_col_index]
                            patronymic = data_row.iloc[patronymic_col_index]
                            policy_num = data_row.iloc[policy_num_col_index]

                            def _as_clean_str(value: object) -> str:
                                if pd.isna(value):
                                    return ""
                                text = str(value).strip()
                                return "" if text.lower() == "nan" else text

                            last_name_s = _as_clean_str(last_name)
                            first_name_s = _as_clean_str(first_name)
                            patronymic_s = _as_clean_str(patronymic)
                            policy_num_s = _as_clean_str(policy_num)

                            if not any(
                                (last_name_s, first_name_s, patronymic_s, policy_num_s)
                            ):
                                empty_streak += 1
                                if empty_streak >= 50:
                                    break
                                continue

                            empty_streak = 0
                            if (
                                last_name_s
                                and first_name_s
                                and patronymic_s
                                and policy_num_s
                            ):
                                full_name = f"{last_name_s} {first_name_s} {patronymic_s}"

                                patients_data.append(
                                    {
                                        "patient_name": full_name,
                                        "insurance_policy_number": policy_num_s,
                                    }
                                )
                    else:
                        print(
                            f"  > В файле {filename} не найдена таблица с пациентами (не найдены заголовки)."
                        )

                except Exception as e:
                    print(f"Произошла ошибка при обработке файла {filename}: {e}")

    return finalize_and_chunk_patients(form_data, patients_data, chunk_size=200)
