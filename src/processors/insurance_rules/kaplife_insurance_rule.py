import re

from aiohttp import FormData
from bs4 import BeautifulSoup

from src.processors.utils.date_helpers import extract_date_range
from src.processors.utils.form_data_finalize import finalize_and_add_patients_json
from src.processors.utils.formatters import clean_message_text
from src.processors.utils.pdf_parser import extract_text_from_pdf


def _normalize_pdf_text(text: str) -> str:
    text = text.replace("\xa0", " ")
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r"([А-Яа-яЁё])(?=\d)", r"\1 ", text)
    text = re.sub(r"(\d)(?=[А-Яа-яЁё])", r"\1 ", text)
    text = re.sub(
        r"(\d{2}\.\d{2}\.\d{2,4})(?=\d{2}\.\d{2}\.\d{2,4})", r"\1 ", text
    )
    return text


def _extract_kaplife_dates(text: str) -> tuple[str | None, str | None]:
    date_from, date_to = extract_date_range(
        text,
        r"Полис\s*№\s*[A-Z0-9\-/ ]{3,}\s*[cс]\s*(\d{2}\.\d{2}\.\d{2,4})\s*(?:по|до)\s*(\d{2}\.\d{2}\.\d{2,4})",
        flags=re.IGNORECASE,
    )

    if not date_from or not date_to:
        fallback = extract_date_range(
            text,
            r"Период\s+действия\s+письма\s*[-–—]?\s*[cс]\s*(\d{2}\.\d{2}\.\d{2,4})\s*(?:по|до)\s*(\d{2}\.\d{2}\.\d{2,4})",
            flags=re.IGNORECASE,
        )
        date_from = date_from or fallback[0]
        date_to = date_to or fallback[1]

    if not date_from or not date_to:
        generic = extract_date_range(
            text,
            r"[cс]\s*(\d{2}\.\d{2}\.\d{2,4})\s*(?:по|до)\s*(\d{2}\.\d{2}\.\d{2,4})",
            flags=re.IGNORECASE,
        )
        date_from = date_from or generic[0]
        date_to = date_to or generic[1]

    return date_from, date_to


def kaplife_insurance_rule(
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

            if filename.lower().endswith(".pdf"):
                try:
                    pdf_text = extract_text_from_pdf(file_bytes)
                    if not pdf_text:
                        print(f"В файле '{filename}' не удалось извлечь текст")
                        continue

                    text_spaced = _normalize_pdf_text(pdf_text)

                    fio_word = r"[А-ЯЁ][А-ЯЁа-яё]+"
                    fio_patterns = [
                        rf"Застрахованн\w*\s*[:\-]?\s*({fio_word}(?:\s+{fio_word}){{1,2}})",
                        rf"Страхователь\s*[:\-]?\s*({fio_word}(?:\s+{fio_word}){{1,2}})",
                    ]
                    patient_fio = None
                    for pat in fio_patterns:
                        fio_match = re.search(pat, text_spaced, flags=re.IGNORECASE)
                        if fio_match:
                            patient_fio = fio_match.group(1).strip()
                            break

                    policy_match = re.search(
                        r"Полис\s*№\s*([0-9A-Z][0-9A-Z\-/ ]+)",
                        text_spaced,
                        flags=re.IGNORECASE,
                    )
                    policy_number = None
                    if policy_match:
                        policy_number = policy_match.group(1).replace(" ", "").strip()

                    date_from, date_to = _extract_kaplife_dates(text_spaced)

                    if patient_fio and policy_number:
                        patient_obj: dict[str, str] = {
                            "patient_name": patient_fio,
                            "insurance_policy_number": policy_number,
                        }
                        if date_from:
                            patient_obj["date_from"] = date_from
                        if date_to:
                            patient_obj["date_to"] = date_to
                        print(
                            f"Из PDF '{filename}' извлечено: ФИО='{patient_fio}', Полис='{policy_number}'"
                        )
                        patients_data.append(patient_obj)
                    else:
                        print(f"В файле '{filename}' не удалось найти ФИО или полис")
                except Exception as e:
                    print(f"Ошибка при обработке PDF-файла '{filename}': {e}")

    finalize_and_add_patients_json(form_data, patients_data)

    return form_data
