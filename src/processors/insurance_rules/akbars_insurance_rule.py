import re
from datetime import datetime

from aiohttp import FormData
from bs4 import BeautifulSoup

from src.processors.utils.doc_parser import extract_text_from_doc
from src.processors.utils.form_data_finalize import (
    finalize_and_add_patients_json,
)
from src.processors.utils.formatters import clean_message_text


def _normalize_doc_text(text: str) -> str:
    text = text.replace("\xa0", " ")
    return re.sub(r"\s+", " ", text).strip()


def _format_date(value: str) -> str:
    value = value.strip()
    for fmt in ("%d.%m.%Y", "%d.%m.%y"):
        try:
            return datetime.strptime(value, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return value


def _append_patient(patients_data: list[dict[str, str]], patient_obj: dict[str, str]) -> None:
    key = (patient_obj.get("patient_name"), patient_obj.get("insurance_policy_number"))
    if not key[0] or not key[1]:
        return
    for existing in patients_data:
        if (existing.get("patient_name"), existing.get("insurance_policy_number")) == key:
            return
    patients_data.append(patient_obj)


def akbars_insurance_rule(
    content: str | None,
    subject: str,
    sender: str,
    attachments: list[tuple[str, bytes]] | None,
) -> FormData:

    form_data = FormData()

    full_name = None
    policy_number = None
    match = re.search(
        r"([А-ЯЁ][а-яё]+\s+[А-ЯЁ][а-яё]+\s+[А-ЯЁ][а-яё]+)\s+([А-ЯЁ\d-]+/\d+)",
        subject,
    )

    if match:
        full_name = match.group(1)
        policy_number = match.group(2)

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
            form_data.add_field(
                "files",
                file_bytes,
                filename=filename,
            )
            if filename.lower().endswith(".doc"):
                try:
                    doc_text = extract_text_from_doc(file_bytes)
                    if not doc_text:
                        print(f"В файле '{filename}' не удалось извлечь текст")
                        continue

                    text_spaced = _normalize_doc_text(doc_text)

                    patient_fio = None
                    policy_from_doc = None
                    date_from = None
                    date_to = None

                    fio_match = re.search(
                        r"([А-ЯЁ][А-ЯЁа-яё]+(?:\s+[А-ЯЁ][А-ЯЁа-яё]+){1,2})\s+\d{2}\.\d{2}\.\d{2,4}",
                        text_spaced,
                    )
                    if fio_match:
                        patient_fio = fio_match.group(1).strip()

                    policy_patterns = [
                        r"Полис\s+([A-ZА-ЯЁ0-9-]+(?:/\d+)?)",
                        r"Полис\s+([A-ZА-ЯЁ0-9-\/]+)",
                    ]
                    for pat in policy_patterns:
                        m = re.search(pat, text_spaced, flags=re.IGNORECASE)
                        if m:
                            policy_from_doc = m.group(1).strip()
                            break

                    date_range_pattern = (
                        r"действителен\s*[сc]\s*(\d{2}\.\d{2}\.\d{2,4})"
                        r"\s*по\s*(\d{2}\.\d{2}\.\d{2,4})"
                    )
                    date_match = re.search(
                        date_range_pattern, text_spaced, flags=re.IGNORECASE
                    )
                    if date_match:
                        date_from = _format_date(date_match.group(1))
                        date_to = _format_date(date_match.group(2))

                    patient_obj: dict[str, str] = {
                        "patient_name": patient_fio or full_name,
                        "insurance_policy_number": policy_from_doc or policy_number,
                    }
                    if date_from:
                        patient_obj["date_from"] = date_from
                    if date_to:
                        patient_obj["date_to"] = date_to

                    if patient_obj["patient_name"] and patient_obj["insurance_policy_number"]:
                        print(
                            f"Из DOC '{filename}' извлечено: ФИО='{patient_obj['patient_name']}', Полис='{patient_obj['insurance_policy_number']}'"
                        )
                        _append_patient(patients_data, patient_obj)
                    else:
                        print(f"В файле '{filename}' не удалось найти ФИО или полис")
                except Exception as exc:
                    print(f"Ошибка при обработке DOC-файла '{filename}': {exc}")

    if full_name and policy_number:
        _append_patient(
            patients_data,
            {
                "patient_name": full_name,
                "insurance_policy_number": policy_number,
            },
        )
    finalize_and_add_patients_json(form_data, patients_data)

    return form_data
