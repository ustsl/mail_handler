import re
import io
from aiohttp import FormData
from bs4 import BeautifulSoup
import pandas as pd


from src.processors.utils.pdf_parser import extract_text_from_pdf
from src.processors.utils.form_data_finalize import finalize_and_add_patients_json
from src.processors.utils.formatters import clean_message_text
import re
import io
import pandas as pd
from bs4 import BeautifulSoup


def fix_encoding(text: str) -> str:
    """
    Исправляет текст, который был в кодировке KOI8-R, но ошибочно прочитан как CP1251.
    """
    try:
        return text.encode("cp1251").decode("koi8-r")
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
                        fio_pattern = r"ФИО Дата\nрождения\n№ Полиса Страхователь № Договора ДМС\n([А-ЯЁ\s]+?)\s+\d{2}\.\d{2}\.\d{4}"
                        fio_match = re.search(fio_pattern, pdf_text)

                        policy_pattern = (
                            r"№ Договора ДМС[\s\S]+?(\d+-\d+)\s*\nОплата будет"
                        )
                        policy_match = re.search(policy_pattern, pdf_text)

                        if fio_match and policy_match:
                            patient_fio = fio_match.group(1).replace("\n", " ").strip()
                            policy_number = policy_match.group(1).strip()

                            patients_data.append(
                                {
                                    "patient_name": patient_fio,
                                    "insurance_policy_number": policy_number,
                                }
                            )
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
