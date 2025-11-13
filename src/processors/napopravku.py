import re

from bs4 import BeautifulSoup

from src.processors.utils.formatters import clean_message_text, format_phone


def napopravku_parse_email(content, subject, sender, attachments):
    soup = BeautifulSoup(content, "html.parser")

    for style in soup.find_all("style"):
        style.decompose()

    raw_text = soup.get_text(separator="\n")
    cleaned_text = clean_message_text(raw_text)

    phone_match = re.search(r"Телефон:\s*([\d\+\-\s\(\)]+)", raw_text)
    phone = format_phone(phone_match.group(1)) if phone_match else ""

    name_match = re.search(r"Имя:\s*(.+)", raw_text)
    name = name_match.group(1).strip() if name_match else ""

    result = {
        "name": name,
        "phone": phone,
        "data": {
            "message": cleaned_text,
        },
        "source": "napopravku",
    }

    return result
