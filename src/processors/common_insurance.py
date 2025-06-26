from bs4 import BeautifulSoup
from aiohttp import FormData

# Предполагается, что эта функция импортирована из вашего проекта
from src.processors.utils.formatters import clean_message_text


def common_insurance_rule(
    content: str | None,
    subject: str,
    sender: str,
    attachments: list[tuple[str, bytes]] | None,
) -> FormData:

    # 1. Создаем экземпляр FormData
    form_data = FormData()

    # 2. Обрабатываем текстовое содержимое письма
    cleaned_text = ""
    if content:
        soup = BeautifulSoup(content, "html.parser")

        # Удаляем все теги <style> для очистки
        for style in soup.find_all("style"):
            style.decompose()

        # Извлекаем сырой текст с разделителем в виде новой строки
        raw_text = soup.get_text(separator="\n")
        cleaned_text = clean_message_text(raw_text)

    # 3. Добавляем текстовые поля в FormData
    form_data.add_field("insurance_email_sender", sender)
    form_data.add_field("subject", subject)
    form_data.add_field("original_message", cleaned_text)

    # 4. Добавляем файлы (вложения) в FormData, если они есть
    if attachments:
        for filename, file_bytes in attachments:
            form_data.add_field(
                "files",
                file_bytes,
                filename=filename,
            )

    return form_data
