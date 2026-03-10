import re

from aiohttp import FormData
from bs4 import BeautifulSoup
from striprtf.striprtf import rtf_to_text

from src.processors.utils.date_helpers import extract_date_range
from src.processors.utils.form_data_finalize import \
    finalize_and_add_patients_json
from src.processors.utils.formatters import clean_message_text

NAME_WORD_RE = r"[А-ЯЁ][А-ЯЁа-яё-]+"
NAME_RE = rf"{NAME_WORD_RE}(?:\s+{NAME_WORD_RE}){{1,3}}"
POLICY_RE = r"[0-9A-ZА-ЯЁ][0-9A-ZА-ЯЁ\-/ ]*/\d{2,4}(?:-[0-9A-ZА-ЯЁ]+)?"


def _normalize_text(text: str) -> str:
    normalized = text.replace("\xa0", " ").replace("\r", "\n")
    normalized = re.sub(r"[ \t\f\v]+", " ", normalized)
    normalized = re.sub(r"\n+", "\n", normalized)
    return normalized.strip()


def _normalize_policy(policy: str) -> str:
    return re.sub(r"\s+", "", policy).strip(" .,:;|")


def _extract_reso_dates(text: str) -> tuple[str | None, str | None]:
    flattened = re.sub(r"\s+", " ", text).strip()
    date_from = None
    date_to = None

    letter_range = extract_date_range(
        flattened,
        r"Срок\s+действия\s+(?:гарантийного\s+)?письма\s*[:\-]?\s*[cс]\s*(\d{2}[./]\d{2}[./]\d{2,4})\s*(?:по|до)\s*(\d{2}[./]\d{2}[./]\d{2,4})",
        flags=re.IGNORECASE,
    )
    date_from = date_from or letter_range[0]
    date_to = date_to or letter_range[1]

    if not date_from or not date_to:
        policy_range = extract_date_range(
            flattened,
            r"Срок\s+действия\s+полиса\s*[:\-]?\s*[cс]\s*(\d{2}[./]\d{2}[./]\d{2,4})\s*(?:по|до)\s*(\d{2}[./]\d{2}[./]\d{2,4})",
            flags=re.IGNORECASE,
        )
        date_from = date_from or policy_range[0]
        date_to = date_to or policy_range[1]

    if not date_from or not date_to:
        fallback_range = extract_date_range(
            flattened,
            r"[cс]\s*(\d{2}[./]\d{2}[./]\d{2,4})\s*(?:по|до)\s*(\d{2}[./]\d{2}[./]\d{2,4})",
            flags=re.IGNORECASE,
        )
        date_from = date_from or fallback_range[0]
        date_to = date_to or fallback_range[1]

    return date_from, date_to


def _append_or_merge_patient(
    patients_data: list[dict[str, str]],
    patient_obj: dict[str, str],
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


def _extract_patients_from_text(text: str) -> list[dict[str, str]]:
    normalized_text = _normalize_text(text)
    date_from, date_to = _extract_reso_dates(normalized_text)
    parsed: list[dict[str, str]] = []

    def append_patient(name: str, policy: str) -> None:
        patient_name = name.strip(" ,.|")
        policy_number = _normalize_policy(policy)
        if not patient_name or not policy_number:
            return

        patient_obj: dict[str, str] = {
            "patient_name": patient_name,
            "insurance_policy_number": policy_number,
        }
        if date_from:
            patient_obj["date_from"] = date_from
        if date_to:
            patient_obj["date_to"] = date_to
        _append_or_merge_patient(parsed, patient_obj)

    table_pat = re.compile(
        rf"^\s*\d+\s*\|\s*({POLICY_RE})\s*\|\s*({NAME_RE})\s*(?:\||$)",
        re.MULTILINE | re.IGNORECASE,
    )
    for policy, name in table_pat.findall(normalized_text):
        append_patient(name, policy)

    insured_near_pat = re.compile(
        rf"застрахован\w*\s*[:\-]?\s*({NAME_RE})",
        re.IGNORECASE,
    )
    insured_names_positions = [
        (match.start(), match.group(1).strip(" ,.|"))
        for match in insured_near_pat.finditer(normalized_text)
    ]

    policy_occ_pat = re.compile(
        rf"(?:номер\s+полиса|полис(?:а)?)\s*[:№\-]?\s*({POLICY_RE})",
        re.IGNORECASE,
    )
    for match in policy_occ_pat.finditer(normalized_text):
        policy = match.group(1)
        name = ""

        window_start = max(0, match.start() - 260)
        before = normalized_text[window_start : match.start()]
        name_before = re.findall(rf"({NAME_RE})(?=[,\s]|$)", before)
        if name_before:
            name = name_before[-1].strip(" ,.|")

        if not name and insured_names_positions:
            prev = [fio for pos, fio in insured_names_positions if pos <= match.start()]
            if prev:
                name = prev[-1]

        if name:
            append_patient(name, policy)

    if not parsed and insured_names_positions:
        first_policy = re.search(rf"\b({POLICY_RE})\b", normalized_text, re.IGNORECASE)
        if first_policy:
            append_patient(insured_names_positions[0][1], first_policy.group(1))

    return parsed


def reso_insurance_rule(
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

    if cleaned_text:
        for patient_obj in _extract_patients_from_text(cleaned_text):
            _append_or_merge_patient(patients_data, patient_obj)

    if attachments:
        for filename, file_bytes in attachments:
            form_data.add_field("files", file_bytes, filename=filename)

            if filename.lower().endswith(".rtf"):
                try:
                    for enc in ("utf-8", "cp1251", "windows-1251", "latin-1"):
                        try:
                            rtf_content = file_bytes.decode(enc)
                            break
                        except UnicodeDecodeError:
                            continue
                    else:
                        rtf_content = file_bytes.decode("utf-8", errors="replace")

                    plain_text = rtf_to_text(rtf_content)
                    for patient_obj in _extract_patients_from_text(plain_text):
                        _append_or_merge_patient(patients_data, patient_obj)

                except Exception as e:
                    print(f"Ошибка при обработке RTF-файла '{filename}': {e}")

    finalize_and_add_patients_json(form_data, patients_data)
    return form_data
