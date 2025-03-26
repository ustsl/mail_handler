import asyncio
from src.query_worker.request_sender import send_request
from src.processors.prodoctorov import prodoctorov_parse_email
from src.email_worker.lib.mail_parser import EmailParser
from src.email_worker.lib.mail_client import MailClient
from src.email_worker.schema import MailCheckSettings
from src.query_worker.schema import QueryRules, HTTPMethod


# Асинхронная функция для отправки HTTP-запроса


def apply_rule_action(rule, email_body: str):
    """
    Обработка действия правила:
      - Передаёт тело письма через процессор (если он задан)
      - Выполняет HTTP-запрос с обработанным телом
    """
    processed_body = (
        rule.action.processor(email_body) if rule.action.processor else email_body
    )
    print(
        f"Выполняется запрос {rule.action.type} к {rule.action.url} с обработанным телом."
    )
    # Выполнение асинхронного запроса в синхронном контексте
    result = asyncio.run(
        send_request(
            rule.action.type,
            rule.action.url,
            headers=rule.action.headers,
            body=processed_body,
        )
    )
    print("Результат запроса:", result)


def check_mail(settings: MailCheckSettings, rules: QueryRules):
    """
    Функция для проверки и обработки новой почты.
    Для каждого письма:
      - Выводятся тема, отправитель и результат обработки через prodoctorov_parse_email.
      - Если тема письма содержит указанный фрагмент и (если указан) совпадает отправитель,
        то тело письма передаётся через процессор из правила, и выполняется HTTP-запрос согласно действию.
    """
    try:
        # Создаём клиента и устанавливаем соединение
        client = MailClient(settings)
        client.connect()

        # Поиск непрочитанных писем
        mail_ids = client.search_unseen()
        if mail_ids:
            print(f"Найдено {len(mail_ids)} новых писем.")

        # Обработка каждого письма
        for mail_id in mail_ids:
            msg = client.fetch_email(mail_id)
            subject = EmailParser.decode_subject(msg.get("Subject"))
            sender_raw = msg.get("From")
            sender = (
                EmailParser.decode_sender(sender_raw)
                if sender_raw
                else "Неизвестный отправитель"
            )

            print("Новая почта:")
            print("Тема:", subject)
            print("Отправитель:", sender)

            body = EmailParser.get_body(msg)

            for rule in rules.root:
                subject_match = (
                    rule.rule.subject.lower() in subject.lower()
                    if rule.rule.subject
                    else True
                )
                sender_match = (
                    sender.lower() == rule.rule.sender.lower()
                    if rule.rule.sender
                    else True
                )
                if subject_match and sender_match:
                    print("Письмо соответствует правилу. Выполняем действие:")
                    apply_rule_action(rule, body)

            # Помечаем письмо как прочитанное
            client.mark_as_seen(mail_id)

        client.logout()

    except Exception as e:
        print("Произошла ошибка:", e)
