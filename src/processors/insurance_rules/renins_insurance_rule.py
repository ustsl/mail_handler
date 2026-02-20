import io
import re
from typing import Optional

import pandas as pd
from aiohttp import FormData
from bs4 import BeautifulSoup

from src.processors.utils.date_helpers import normalize_date
from src.processors.utils.doc_parser import extract_text_from_doc
from src.processors.utils.form_data_finalize import \
    finalize_and_add_patients_json
from src.processors.utils.formatters import clean_message_text
from src.processors.utils.pdf_parser import extract_text_from_pdf


def _normalize_text_for_search(text: str) -> str:
    text = text.replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text).strip()
    return text


def _extract_doc_utf16_fallback_text(doc_bytes: bytes) -> str:
    try:
        decoded = doc_bytes.decode("utf-16le", errors="ignore")
    except Exception:
        return ""

    # Keep readable Cyrillic/Latin text and separators, replace binary noise with spaces.
    filtered = re.sub(
        r"[^0-9A-Za-zА-Яа-яЁё\s:/().,\"'№\-]",
        " ",
        decoded,
    )
    return _normalize_text_for_search(filtered)


def _normalize_date_candidate(value: str) -> str | None:
    candidate = value.strip()
    candidate = re.sub(r"\s*[гg]\.?\s*$", "", candidate, flags=re.IGNORECASE)
    candidate = candidate.replace("/", ".")
    return normalize_date(candidate)


def _extract_renins_dates(text: str) -> tuple[str | None, str | None]:
    date_from = None
    date_to = None

    range_match = re.search(
        r"[cс]\s*(\d{2}[./]\d{2}[./]\d{2,4})\s*(?:по|до)\s*(\d{2}[./]\d{2}[./]\d{2,4})",
        text,
        flags=re.IGNORECASE,
    )
    if range_match:
        date_from = _normalize_date_candidate(range_match.group(1))
        date_to = _normalize_date_candidate(range_match.group(2))

    if not date_to:
        end_match = re.search(
            r"окончания\s+действия\s+полиса\s*[-–—:]?\s*(\d{2}[./]\d{2}[./]\d{2,4})",
            text,
            flags=re.IGNORECASE,
        )
        if end_match:
            date_to = _normalize_date_candidate(end_match.group(1))

    if not date_to:
        fallback_end_match = re.search(
            r"действительно\s*(?:до|по)\s*(\d{2}[./]\d{2}[./]\d{2,4})",
            text,
            flags=re.IGNORECASE,
        )
        if fallback_end_match:
            date_to = _normalize_date_candidate(fallback_end_match.group(1))

    if not date_from:
        issue_date_match = re.search(
            r"\bот\s*(\d{2}[./]\d{2}[./]\d{2,4})\s*[гg]?\b",
            text,
            flags=re.IGNORECASE,
        )
        if issue_date_match:
            date_from = _normalize_date_candidate(issue_date_match.group(1))

    return date_from, date_to


def _build_patient_obj(
    patient_fio: str, policy_number: str, source_text: str
) -> dict[str, str]:
    patient_obj = {
        "patient_name": patient_fio,
        "insurance_policy_number": policy_number,
    }
    date_from, date_to = _extract_renins_dates(source_text)
    if date_from:
        patient_obj["date_from"] = date_from
    if date_to:
        patient_obj["date_to"] = date_to
    return patient_obj


def _extract_patient_from_doc_text(text: str) -> dict[str, str] | None:
    normalized_text = _normalize_text_for_search(text)

    fio_patterns = [
        (
            r"Застрахован(?:ный|ная|ное)?\s*[:\-]?\s*"
            r"([А-ЯЁ][А-ЯЁа-яё-]+(?:\s+[А-ЯЁ][А-ЯЁа-яё-]+){2})"
        ),
        (
            r"на\s+имя\s*"
            r"([А-ЯЁ][А-ЯЁа-яё-]+(?:\s+[А-ЯЁ][А-ЯЁа-яё-]+){2})"
        ),
    ]
    patient_fio = ""
    for pattern in fio_patterns:
        fio_match = re.search(pattern, normalized_text, flags=re.IGNORECASE)
        if fio_match:
            patient_fio = fio_match.group(1).strip()
            break

    policy_patterns = [
        r"Страховой\s+полис\s*[:№\-]?\s*([0-9A-ZА-ЯЁ][0-9A-ZА-ЯЁ/\-]+)",
        r"Номер\s+полиса\s*[:№\-]?\s*([0-9A-ZА-ЯЁ][0-9A-ZА-ЯЁ/\-]+)",
    ]
    policy_number = ""
    for pattern in policy_patterns:
        policy_match = re.search(pattern, normalized_text, flags=re.IGNORECASE)
        if policy_match:
            policy_number = policy_match.group(1).strip()
            break

    if not patient_fio or not policy_number:
        return None

    return _build_patient_obj(patient_fio, policy_number, normalized_text)


def _extract_patient_from_pdf_text(text: str) -> dict[str, str] | None:
    normalized_text = _normalize_text_for_search(text)

    fio_match = re.search(
        r"на\s+имя\s*([А-ЯЁ][А-ЯЁа-яё-]+(?:\s+[А-ЯЁ][А-ЯЁа-яё-]+){2})",
        normalized_text,
        flags=re.IGNORECASE,
    )
    patient_fio = fio_match.group(1).strip() if fio_match else ""

    policy_match = re.search(
        r"Номер\s+полиса\s*[:№\-]?\s*([0-9A-ZА-ЯЁ][0-9A-ZА-ЯЁ/\-]+)",
        normalized_text,
        flags=re.IGNORECASE,
    )
    policy_number = policy_match.group(1).strip() if policy_match else ""

    if not patient_fio or not policy_number:
        return None

    return _build_patient_obj(patient_fio, policy_number, normalized_text)


def _append_or_merge_patient(
    patients_data: list[dict[str, str]], patient_obj: dict[str, str]
) -> None:
    key = (patient_obj.get("patient_name"), patient_obj.get("insurance_policy_number"))
    if not key[0] or not key[1]:
        return

    for existing in patients_data:
        if (
            existing.get("patient_name"),
            existing.get("insurance_policy_number"),
        ) == key:
            if not existing.get("date_from") and patient_obj.get("date_from"):
                existing["date_from"] = patient_obj["date_from"]
            if not existing.get("date_to") and patient_obj.get("date_to"):
                existing["date_to"] = patient_obj["date_to"]
            return

    patients_data.append(patient_obj)


def renins_insurance_rule(
    content: Optional[str],
    subject: str,
    sender: str,
    attachments: Optional[list[tuple[str, bytes]]],
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

    if cleaned_text:
        patient_from_content = _extract_patient_from_pdf_text(cleaned_text)
        if patient_from_content:
            _append_or_merge_patient(patients_data, patient_from_content)

    if attachments:
        for filename, file_bytes in attachments:
            form_data.add_field("files", file_bytes, filename=filename)

            if filename.lower().endswith(".doc"):
                try:
                    doc_text = extract_text_from_doc(file_bytes)
                    if not doc_text:
                        print(f"В файле '{filename}' не удалось извлечь текст")
                    else:
                        patient_obj = _extract_patient_from_doc_text(doc_text)
                        if not patient_obj:
                            fallback_doc_text = _extract_doc_utf16_fallback_text(
                                file_bytes
                            )
                            if fallback_doc_text:
                                patient_obj = _extract_patient_from_doc_text(
                                    fallback_doc_text
                                )
                        if patient_obj:
                            _append_or_merge_patient(patients_data, patient_obj)
                            print(
                                f"Из DOC '{filename}' извлечено: ФИО='{patient_obj['patient_name']}', Полис='{patient_obj['insurance_policy_number']}'"
                            )
                except Exception as e:
                    print(f"Ошибка при обработке DOC-файла '{filename}': {e}")

            if filename.lower().endswith(".pdf"):
                try:
                    pdf_text = extract_text_from_pdf(file_bytes)
                    if not pdf_text:
                        print(f"В файле '{filename}' не удалось извлечь текст")
                    else:
                        patient_obj = _extract_patient_from_pdf_text(pdf_text)
                        if patient_obj:
                            _append_or_merge_patient(patients_data, patient_obj)
                            print(
                                f"Из PDF '{filename}' извлечено: ФИО='{patient_obj['patient_name']}', Полис='{patient_obj['insurance_policy_number']}'"
                            )
                except Exception as e:
                    print(f"Ошибка при обработке PDF-файла '{filename}': {e}")

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
                                _append_or_merge_patient(
                                    patients_data,
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
