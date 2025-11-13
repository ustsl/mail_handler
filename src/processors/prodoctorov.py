import re

from bs4 import BeautifulSoup

from src.processors.utils.formatters import (clean_message_text, extract_field,
                                             format_phone)


def prodoctorov_parse_email(html_content, subject, sender, attachments):
    """
    Принимает HTML-содержимое письма, извлекает:
      - name (значение после метки "Пациент")
      - phone (значение после метки "Контактный телефон", приводится к формату)
      - data.message - очищенный от HTML текст всего письма (без стилей и фиксов Outlook), разбитый на строки (\n)
      - data.url - ссылка на "Личный кабинет" или "https://medflex.ru/login/", если ссылка не найдена
      - source - жестко задан "prodoctorov"
    """
    # Парсим HTML-контент
    soup = BeautifulSoup(html_content, "html.parser")

    # Удаляем все теги <style>, чтобы куски стилей не попадали в итоговый текст
    for style in soup.find_all("style"):
        style.extract()

    # Извлекаем текст, разделяя элементы символом новой строки
    raw_text = soup.get_text(separator="\n")
    # Очищаем текст: удаляем фиксы Outlook и блок стилей до метки "Личный кабинет"
    cleaned_text = clean_message_text(raw_text)

    # Разбиваем исходный текст на строки для поиска нужных меток
    lines = [line.strip() for line in raw_text.split("\n") if line.strip()]
    name = extract_field(lines, "Пациент")
    phone_raw = extract_field(lines, "Контактный телефон")
    phone = format_phone(phone_raw) if phone_raw else ""

    # Ищем ссылку "Личный кабинет"; если не найдена, устанавливаем дефолтный URL
    login_link_tag = soup.find("a", string=lambda s: s and "кабинет" in s.lower())
    login_link = (
        login_link_tag.get("href") if login_link_tag else "https://medflex.ru/login/"
    )

    result = {
        "name": name or "",
        "phone": phone,
        "data": {
            "message": cleaned_text,
            "url": login_link,
            "additionalInfo": subject,
        },
        "source": "prodoctorov",
    }

    print(result)

    return result
