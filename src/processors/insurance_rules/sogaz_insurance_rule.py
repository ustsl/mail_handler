import json
import re
import io
from aiohttp import FormData
from bs4 import BeautifulSoup
import pandas as pd

from src.processors.utils.form_data_finalize import finalize_and_add_patients_json
from src.processors.utils.pdf_parser import extract_text_from_pdf
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

    patients_data = []

    if attachments:
        for filename, file_bytes in attachments:
            form_data.add_field("files", file_bytes, filename=filename)

            # --- Обработка PDF (без изменений) ---
            if filename.lower().endswith(".pdf"):
                pdf_text = extract_text_from_pdf(file_bytes)
                if pdf_text:
                    patient_fio = ""
                    policy_number = ""
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
                    patients_data.append(
                        {
                            "patient_name": str(patient_fio),
                            "insurance_policy_number": str(policy_number),
                        }
                    )

            if filename.lower().endswith((".xls", ".xlsx")):
                try:
                    df = pd.read_excel(io.BytesIO(file_bytes), header=None)

                    header_row_index = -1
                    last_name_col_index = -1
                    first_name_col_index = -1
                    patronymic_col_index = -1
                    policy_num_col_index = -1

                    # Заголовки, которые мы обязаны найти
                    required_headers = {"Фамилия", "Имя", "Отчество", "№ полиса"}

                    for i, row in df.iterrows():
                        row_values = {str(v).strip() for v in row.values if pd.notna(v)}
                        # Проверяем, что все нужные заголовки есть в строке
                        if required_headers.issubset(row_values):
                            header_row_index = i
                            header_list = [str(v).strip() for v in list(df.iloc[i])]

                            # Находим и сохраняем индексы колонок
                            last_name_col_index = header_list.index("Фамилия")
                            first_name_col_index = header_list.index("Имя")
                            patronymic_col_index = header_list.index("Отчество")
                            policy_num_col_index = header_list.index("№ полиса")
                            break

                    if header_row_index != -1:
                        print(
                            f"  > Заголовок найден в строке {header_row_index} файла '{filename}'. Начинаем сбор данных..."
                        )
                        for i in range(header_row_index + 1, len(df)):
                            data_row = df.iloc[i]
                            first_cell_val = data_row.iloc[0]
                            # Прерываем цикл, если строка не похожа на строку с данными (например, пустая или без номера п/п)
                            if (
                                pd.isna(first_cell_val)
                                or not str(first_cell_val).strip().isdigit()
                            ):
                                break

                            # Извлекаем ФИО и номер полиса по найденным индексам
                            last_name = data_row.iloc[last_name_col_index]
                            first_name = data_row.iloc[first_name_col_index]
                            patronymic = data_row.iloc[patronymic_col_index]
                            policy_num = data_row.iloc[policy_num_col_index]

                            # Добавляем данные, только если все поля присутствуют
                            if (
                                pd.notna(last_name)
                                and pd.notna(first_name)
                                and pd.notna(patronymic)
                                and pd.notna(policy_num)
                            ):
                                # Собираем полное имя в одну строку
                                full_name = f"{str(last_name).strip()} {str(first_name).strip()} {str(patronymic).strip()}"

                                patients_data.append(
                                    {
                                        "patient_name": full_name,
                                        "insurance_policy_number": str(
                                            policy_num
                                        ).strip(),
                                    }
                                )
                    else:
                        print(
                            f"  > В файле {filename} не найдена таблица с пациентами (не найдены заголовки)."
                        )

                except Exception as e:
                    print(f"Произошла ошибка при обработке файла {filename}: {e}")

    finalize_and_add_patients_json(form_data, patients_data)

    return form_data
