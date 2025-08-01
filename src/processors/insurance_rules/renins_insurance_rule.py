import io
import re
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

    if attachments and cleaned_text:

        is_document_attached = any(
            filename.lower().endswith((".pdf", ".doc")) for filename, _ in attachments
        )

        if is_document_attached:
            patient_fio = ""
            policy_number = ""

            fio_pattern = r"на имя\s*([А-Яа-яЁё]+\s+[А-Яа-яЁё]+\s+[А-Яа-яЁё]+)"
            fio_match = re.search(fio_pattern, cleaned_text, re.IGNORECASE)
            if fio_match:
                patient_fio = fio_match.group(1).strip()
            policy_pattern = r"Номер полиса:\s*([\w\d/]+)"
            policy_match = re.search(policy_pattern, cleaned_text, re.IGNORECASE)
            if policy_match:
                policy_number = policy_match.group(1).strip()

            if patient_fio and policy_number:
                print(
                    f"Из тела письма извлечено: ФИО='{patient_fio}', Полис='{policy_number}'"
                )
                patients_data.append(
                    {
                        "patient_name": patient_fio,
                        "insurance_policy_number": policy_number,
                    }
                )

    if attachments:
        for filename, file_bytes in attachments:
            form_data.add_field("files", file_bytes, filename=filename)

            if filename.lower().endswith((".xls", ".xlsx")):
                try:
                    df = pd.read_excel(io.BytesIO(file_bytes), header=None)
                    PATIENT_NAME_KEYWORD = "фамил"
                    POLICY_NUM_KEYWORD = "полис"
                    header_row_index, patient_name_col_index, policy_num_col_index = (
                        -1,
                        -1,
                        -1,
                    )

                    for i, row in df.iterrows():
                        row_values = [
                            str(v).lower().strip() for v in row.values if pd.notna(v)
                        ]
                        found_name_col = any(
                            PATIENT_NAME_KEYWORD in val for val in row_values
                        )
                        found_policy_col = any(
                            POLICY_NUM_KEYWORD in val for val in row_values
                        )

                        if found_name_col and found_policy_col:
                            header_row_index = i
                            header_list = [
                                str(v).lower().strip() for v in list(df.iloc[i])
                            ]
                            for col_idx, header_val in enumerate(header_list):
                                if PATIENT_NAME_KEYWORD in header_val:
                                    patient_name_col_index = col_idx
                                if POLICY_NUM_KEYWORD in header_val:
                                    policy_num_col_index = col_idx
                            break

                    if header_row_index != -1:
                        for i in range(header_row_index + 1, len(df)):
                            data_row = df.iloc[i]
                            patient_name = data_row.iloc[patient_name_col_index]
                            policy_num = data_row.iloc[policy_num_col_index]
                            if pd.isna(patient_name) and pd.isna(policy_num):
                                break
                            if pd.notna(patient_name) and pd.notna(policy_num):
                                patients_data.append(
                                    {
                                        "patient_name": str(patient_name).strip(),
                                        "insurance_policy_number": str(
                                            policy_num
                                        ).strip(),
                                    }
                                )
                except Exception as e:
                    print(f"Произошла ошибка при обработке Excel файла {filename}: {e}")

    finalize_and_add_patients_json(form_data, patients_data)

    return form_data
