import io
import json
import pandas as pd
from aiohttp import FormData
from bs4 import BeautifulSoup
from typing import List, Tuple, Optional

from src.processors.utils.form_data_finalize import finalize_and_add_patients_json
from src.processors.utils.formatters import clean_message_text


def renins_insurance_rule(
    content: Optional[str],
    subject: str,
    sender: str,
    attachments: Optional[List[Tuple[str, bytes]]],
) -> FormData:

    form_data = FormData()

    # 1. Подготовка текстовых полей
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

            if filename.lower().endswith((".xls", ".xlsx")):
                try:
                    df = pd.read_excel(io.BytesIO(file_bytes), header=None)

                    header_row_index = -1
                    patient_name_col_index = -1
                    policy_num_col_index = -1

                    for i, row in df.iterrows():
                        row_values = [str(v).strip() for v in row.values if pd.notna(v)]
                        if "Фамилия" in row_values and "№ полиса" in row_values:
                            header_row_index = i
                            header_list = [str(v).strip() for v in list(df.iloc[i])]
                            patient_name_col_index = header_list.index("Фамилия")
                            policy_num_col_index = header_list.index("№ полиса")
                            break

                    if header_row_index != -1:
                        print(
                            f"  > Заголовок найден в строке {header_row_index}. Начинаем сбор данных..."
                        )
                        for i in range(header_row_index + 1, len(df)):
                            data_row = df.iloc[i]
                            first_cell_val = data_row.iloc[0]
                            if (
                                pd.isna(first_cell_val)
                                or not str(first_cell_val).strip().isdigit()
                            ):
                                break

                            patient_name = data_row.iloc[patient_name_col_index]
                            policy_num = data_row.iloc[policy_num_col_index]

                            if pd.notna(patient_name) and pd.notna(policy_num):
                                patients_data.append(
                                    {
                                        "patient_name": str(patient_name),
                                        "insurance_policy_number": str(policy_num),
                                    }
                                )
                    else:
                        print(
                            f"  > В файле {filename} не найдена таблица с пациентами."
                        )

                except Exception as e:
                    print(f"Произошла ошибка при обработке файла {filename}: {e}")

    finalize_and_add_patients_json(form_data, patients_data)

    return form_data
