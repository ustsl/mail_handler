import re

from bs4 import BeautifulSoup

from src.processors.utils.formatters import clean_message_text, format_phone


def sber_parse_email(content, subject, sender):
    """
    Принимает HTML-содержимое письма и:
      - Извлекает имя пациента (строка после метки "Имя пациента:")
      - Извлекает номер телефона (строка после метки "Телефон:")
      - Очищает весь контент от HTML и лишних пробелов
      - Возвращает словарь с ключами: name, phone, data (с сообщением и темой письма) и source="sber"
    """
    # Парсинг HTML
    soup = BeautifulSoup(content, "html.parser")

    # Удаляем все теги <style>
    for style in soup.find_all("style"):
        style.decompose()

    # Извлекаем сырой текст с разделителем в виде новой строки
    raw_text = soup.get_text(separator="\n")
    cleaned_text = clean_message_text(raw_text)

    # Извлечение номера телефона (ищем строку, начинающуюся с "Телефон:")
    phone_match = re.search(r"Телефон:\s*([\+\d\(\)\s-]+)", raw_text)
    phone = format_phone(phone_match.group(1)) if phone_match else ""

    # Извлечение имени пациента (ищем строку с "Имя пациента:")
    name_match = re.search(r"Имя пациента:\s*(.+)", raw_text)
    name = name_match.group(1).strip() if name_match else ""

    result = {
        "name": name,
        "phone": phone,
        "data": {
            "message": cleaned_text,
            "additionalInfo": subject,
        },
        "source": "sber",
    }

    return result
