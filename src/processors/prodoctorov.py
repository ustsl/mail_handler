import re
from bs4 import BeautifulSoup


def format_phone(phone_str):
    """
    Приводит номер телефона к формату 79126683852:
      - Убирает все нецифровые символы
      - Если номер начинается с "8", заменяет её на "7"
    """
    digits = "".join(filter(str.isdigit, phone_str))
    if digits.startswith("8"):
        digits = "7" + digits[1:]
    return digits


def extract_field(lines, label):
    """
    Ищет в списке строк строку с указанной меткой и возвращает значение из следующей строки.
    """
    for i, line in enumerate(lines):
        if label.lower() in line.lower():
            if i + 1 < len(lines):
                return lines[i + 1].strip()
    return None


def clean_message_text(text):
    """
    Очищает текст:
      - Заменяет неразрывные пробелы на обычные
      - Удаляет строчку "/* Фиксы для Outlook конец*/"
      - Удаляет блок стилей, если он присутствует, до метки "Личный кабинет"
      - Удаляет лишние пробелы по краям каждой строки
      - Сохраняет структуру блоков, разделяя строки символом новой строки
    """
    # Заменяем неразрывные пробелы
    text = text.replace("\xa0", " ")
    # Удаляем строчку с фиксом для Outlook, если она встречается
    text = re.sub(r"/\*\s*Фиксы\s+для\s+Outlook\s+конец\s*\*/", "", text)
    # Если во входном тексте присутствует блок стилей, удаляем всё до метки "Личный кабинет"
    marker = "Личный кабинет"
    if marker in text:
        text = text[text.find(marker) :]
    # Разбиваем текст по символу новой строки, очищаем каждую строку и отбрасываем пустые
    lines = [line.strip() for line in text.split("\n") if line.strip()]
    return "\n".join(lines)


def prodoctorov_parse_email(html_content, subject, sender):
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

    return result
