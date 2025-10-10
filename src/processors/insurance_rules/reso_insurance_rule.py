import re
from aiohttp import FormData
from bs4 import BeautifulSoup

from striprtf.striprtf import rtf_to_text
from src.processors.utils.form_data_finalize import finalize_and_add_patients_json
from src.processors.utils.formatters import clean_message_text


import re
from bs4 import BeautifulSoup
from aiohttp import FormData
from striprtf.striprtf import rtf_to_text


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

    NAME_RE = r"[А-ЯЁ][А-ЯЁ\-]+(?:\s+[А-ЯЁ][А-ЯЁ\-]+){1,3}"
    POLICY_RE = r"[\d\-]+/\d{2}(?:-[\wА-ЯЁ\d]+)?"

    # парсер для произвольного plain_text без "нормализаций"
    def parse_plain_text(plain_text: str) -> list[dict[str, str]]:
        results: dict[str, str] = {}

        table_pat = re.compile(
            rf"^\s*\d+\s*\|\s*({POLICY_RE})\s*\|\s*({NAME_RE})\s*\|", re.MULTILINE
        )
        for policy, name in table_pat.findall(plain_text):
            results[policy.strip()] = name.strip(" ,.|")

        insured_near_pat = re.compile(
            rf"застрахован\w*:\s*(?:\n|\r|\s)*({NAME_RE})", re.IGNORECASE
        )
        insured_names_positions = [
            (m.start(), m.group(1).strip(" ,.|"))
            for m in insured_near_pat.finditer(plain_text)
        ]

        policy_occ_pat = re.compile(
            rf"(?:номер\s+полиса\s*[:\-]?\s*|№\s*)({POLICY_RE})", re.IGNORECASE
        )
        for m in policy_occ_pat.finditer(plain_text):
            policy = m.group(1).strip()
            if policy in results:
                continue

            name = None
            window_start = max(0, m.start() - 200)
            before = plain_text[window_start : m.start()]
            name_before = re.findall(rf"({NAME_RE})(?:[, ]|$)", before)
            if name_before:
                name = name_before[-1].strip(" ,.|")

            if not name and insured_names_positions:
                prev = [n for pos, n in insured_names_positions if pos <= m.start()]
                if prev:
                    name = prev[-1]

            if name:
                results[policy] = name

        return [
            {"patient_name": v, "insurance_policy_number": k}
            for k, v in results.items()
        ]

    # 1) Парсинг тела письма
    if cleaned_text:
        patients_data.extend(parse_plain_text(cleaned_text))

    # 2) Парсинг вложений
    if attachments:
        for filename, file_bytes in attachments:
            form_data.add_field("files", file_bytes, filename=filename)

            if filename.lower().endswith(".rtf"):
                try:
                    tried = []
                    for enc in ("utf-8", "cp1251", "windows-1251", "latin-1"):
                        try:
                            rtf_content = file_bytes.decode(enc)
                            break
                        except UnicodeDecodeError:
                            tried.append(enc)
                    else:
                        rtf_content = file_bytes.decode("utf-8", errors="replace")

                    plain_text = rtf_to_text(rtf_content)
                    patients_data.extend(parse_plain_text(plain_text))

                except Exception as e:
                    print(f"Ошибка при обработке RTF-файла '{filename}': {e}")

    finalize_and_add_patients_json(form_data, patients_data)
    return form_data
