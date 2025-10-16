import re

from aiohttp import FormData
from bs4 import BeautifulSoup

from src.processors.utils.pdf_parser import extract_text_from_pdf
from src.processors.utils.form_data_finalize import finalize_and_add_patients_json
from src.processors.utils.formatters import clean_message_text


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
