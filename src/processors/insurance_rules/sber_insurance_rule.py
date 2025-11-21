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
    universal_search_table_func_v2
from src.processors.utils.zip_extractors import extract_first_file_from_zip


def sber_insurance_rule(
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

                # Ищем ФИО
                fio_pattern = r"ФИО:\s*([А-ЯЁ][а-яё]+(?:\s+[А-ЯЁ][а-яё]+){1,2})"
                fio_match = re.search(fio_pattern, pdf_text)

                # Ищем номер полиса (ID)
                policy_pattern = r"Номер\s+ID\s*\(полис\):\s*(\S+)"
                policy_match = re.search(policy_pattern, pdf_text)

                if fio_match and policy_match:
                    patient_fio = fio_match.group(1).strip()
                    policy_number = policy_match.group(1).strip()
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
                try:
                    pdf_text = extract_text_from_pdf(file_bytes)

                    fio_pattern = r"([А-ЯЁ]{2,}\s[А-ЯЁ]{2,}\s[А-ЯЁ]{2,})"
                    fio_match = re.search(fio_pattern, pdf_text)

                    policy_pattern = r"Номер полиса\s*(\S+)"
                    policy_match = re.search(policy_pattern, pdf_text)

                    if fio_match and policy_match:
                        patient_fio = fio_match.group(1).strip()
                        policy_number = policy_match.group(1).strip()
                        print(
                            f"Из PDF '{filename}' извлечено: ФИО='{patient_fio}', Полис='{policy_number}'"
                        )
                        patients_data.append(
                            {
                                "patient_name": patient_fio,
                                "insurance_policy_number": policy_number,
                            }
                        )

                except Exception as e:
                    print(f"Ошибка при обработке PDF-файла '{filename}': {e}")

    finalize_and_add_patients_json(form_data, patients_data)

    return form_data


def sber_ins_insurance_rule(
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

                fio_pattern = (
                    r"Застрахованный:\s*([А-ЯЁ][а-яё]+(?:\s+[А-ЯЁ][а-яё]+){1,2})"
                )
                fio_match = re.search(fio_pattern, pdf_text)
                policy_pattern = r"Номер договора:\s*([A-ZА-Я0-9\-]+)"
                policy_match = re.search(policy_pattern, pdf_text)

                if fio_match and policy_match:
                    patient_fio = fio_match.group(1).strip()
                    policy_number = policy_match.group(1).strip()
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
                try:
                    pdf_text = extract_text_from_pdf(file_bytes)

                    fio_pattern = r"([А-ЯЁ]{2,}\s[А-ЯЁ]{2,}\s[А-ЯЁ]{2,})"
                    fio_match = re.search(fio_pattern, pdf_text)

                    policy_pattern = r"Номер полиса\s*(\S+)"
                    policy_match = re.search(policy_pattern, pdf_text)

                    if fio_match and policy_match:
                        patient_fio = fio_match.group(1).strip()
                        policy_number = policy_match.group(1).strip()
                        print(
                            f"Из PDF '{filename}' извлечено: ФИО='{patient_fio}', Полис='{policy_number}'"
                        )
                        patients_data.append(
                            {
                                "patient_name": patient_fio,
                                "insurance_policy_number": policy_number,
                            }
                        )

                except Exception as e:
                    print(f"Ошибка при обработке PDF-файла '{filename}': {e}")

    finalize_and_add_patients_json(form_data, patients_data)

    return form_data


def _generate_four_digit_passwords() -> list[str]:
    return [f"{num:04d}" for num in range(10000)]


def sber_digital_assistant_insurance_rule(
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

    patients_data: list[dict[str, str]] = []

    if attachments:
        for filename, file_bytes in attachments:
            form_data.add_field("files", file_bytes, filename=filename)

            lowered_name = filename.lower()

            def _process_excel_bytes(data: bytes, source_name: str) -> None:
                nonlocal patients_data
                try:
                    df = pd.read_excel(io.BytesIO(data), header=None)
                    patients = universal_search_table_func_v2(
                        df,
                        name_parts_headers=["Фамилия", "Имя", "Отчество"],
                        polis_syn=["№ полиса (ID)"],
                    )
                    patients_data.extend(patients)
                except Exception as e:
                    print(
                        f"Ошибка при обработке Excel-файла '{source_name}' из письма digital.assistant: {e}"
                    )

            if lowered_name.endswith(".xlsx"):
                _process_excel_bytes(file_bytes, filename)
            elif lowered_name.endswith(".zip"):
                extracted = extract_first_file_from_zip(
                    file_bytes,
                    allowed_extensions=(".xls", ".xlsx"),
                    password_candidates=_generate_four_digit_passwords(),
                )
                if extracted:
                    inner_name, inner_bytes = extracted
                    _process_excel_bytes(inner_bytes, inner_name)
                else:
                    print(
                        f"Не удалось извлечь Excel из ZIP '{filename}' для digital.assistant@sberins.ru"
                    )

    finalize_and_add_patients_json(form_data, patients_data)

    return form_data
