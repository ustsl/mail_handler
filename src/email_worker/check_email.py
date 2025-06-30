import asyncio

from src.email_worker.lib.mail_client import MailClient
from src.email_worker.lib.mail_parser import EmailParser
from src.email_worker.schema import MailCheckSettings
from src.query_worker.request_sender import send_request
from src.query_worker.schema import QueryRules


def apply_rule_action(
    rule,
    email_body: str,
    email_subject: str,
    email_sender: str,
    attachments: list[tuple[str, bytes]] | None = None,
):
    """
    Обработка действия правила:
      - Передаёт тело письма и вложения через процессор (если он задан)
      - Выполняет HTTP-запрос с обработанным телом и вложениями.
    """

    processed_body = (
        rule.action.processor(email_body, email_subject, email_sender, attachments)
        if rule.action.processor
        else email_body
    )

    print(
        f"Выполняется запрос {rule.action.type} к {rule.action.url} с обработанным телом."
    )
    if attachments:
        print(f"К запросу прикреплено {len(attachments)} файлов.")

    # Выполнение асинхронного запроса в синхронном контексте
    result = asyncio.run(
        send_request(
            rule.action.type,
            rule.action.url,
            headers=rule.action.headers,
            data=processed_body,
        )
    )
    print(rule.action.url)
    print("Результат запроса:", result)


def check_mail(settings: MailCheckSettings, rules: QueryRules):
    """
    Функция для проверки и обработки новой почты.
    Для каждого письма:
      - Извлекает тело и, если нужно, вложения.
      - Если письмо соответствует правилу, выполняет действие,
        передавая вложения, если правило этого требует.
    """
    try:
        client = MailClient(settings)
        client.connect()

        mail_ids = client.search_unseen()
        if mail_ids:
            print(f"Найдено {len(mail_ids)} новых писем.")

        can_be_marked_as_read = True

        for mail_id in mail_ids:
            msg = client.fetch_email(mail_id)
            subject = EmailParser.decode_subject(msg.get("Subject"))
            sender_raw = msg.get("From")
            sender = (
                EmailParser.decode_sender(sender_raw)
                if sender_raw
                else "Неизвестный отправитель"
            )

            print("\nНовая почта:")
            print("Тема:", subject)
            print("Отправитель:", sender)

            body = EmailParser.get_body(msg)

            is_actual_rule = False

            for rule in rules.root:

                subject_match = (
                    rule.rule.subject.lower() in subject.lower()
                    if rule.rule.subject
                    else True
                )

                sender_match = (
                    (
                        rule.rule.sender.lower() in sender.lower()
                        if rule.rule.sender.lower().startswith("@")
                        else sender.lower() == rule.rule.sender.lower()
                    )
                    if rule.rule.sender
                    else True
                )

                if subject_match and sender_match:
                    is_actual_rule = True
                    print(
                        f"Письмо соответствует правилу (attachments: {rule.attachment_field}). Выполняем действие:"
                    )

                    attachments = None

                    if rule.attachment_field:
                        print("Правило требует обработки вложений. Извлекаем файлы...")
                        attachments = EmailParser.get_attachments(msg)
                        if attachments:
                            print(
                                f"Найдено {len(attachments)} вложений: {[att[0] for att in attachments]}"
                            )
                        else:
                            print("Вложений в письме не найдено.")

                    try:
                        apply_rule_action(rule, body, subject, sender, attachments)
                    except Exception as e:
                        print(f"Произошла ошибка")
                        can_be_marked_as_read = False

            if can_be_marked_as_read:
                client.mark_as_seen(mail_id)

            if not is_actual_rule:
                print(f"Письмо от {sender} не соответствует ни одного из правил")

        client.logout()

    except Exception as e:
        print(f"Произошла ошибка: {e}")
