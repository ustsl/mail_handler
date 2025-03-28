import re


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
