from src.email_worker.lib.mail_client import MailClient
from src.email_worker.lib.mail_parser import EmailParser
from src.email_worker.schema import MailCheckSettings
from src.query_worker.request_sender import send_request
from src.query_worker.schema import QueryRules
from src.outbox.producer import enqueue_json_request


async def apply_rule_action(
    rule,
    email_body: str,
    email_subject: str,
    email_sender: str,
    attachments: list[tuple[str, bytes]] | None = None,
):
    processed_body = (
        rule.action.processor(email_body, email_subject, email_sender, attachments)
        if rule.action.processor
        else email_body
    )

    url = rule.action.url
    try:
        print(f"Подготовка запроса {rule.action.type} к {url}...")

        if isinstance(processed_body, dict):
            await enqueue_json_request(
                method=rule.action.type,
                url=url,
                headers=rule.action.headers,
                json_body=processed_body,
            )
            print("Задание (JSON) поставлено в очередь.")
            return (True, url, None)

        response = await send_request(
            rule.action.type,
            url,
            headers=rule.action.headers,
            data=processed_body,
        )
        print(f"Запрос на {url} успешно выполнен.")
        print(f"  -> Ответ от сервера: {response}")
        return (True, url, None)

    except Exception as e:
        print(f"  [ОШИБКА ЗАПРОСА] При обращении к {url} произошла ошибка: {e}")
        return (False, url, e)


async def check_mail(settings: MailCheckSettings, rules: QueryRules):
    client = MailClient(settings)
    try:
        client.connect()
        mail_ids = client.search_unseen()
        if mail_ids:
            print(f"Найдено {len(mail_ids)} новых писем.")

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
            print("  Тема:", subject)
            print("  Отправитель:", sender)
            body = EmailParser.get_body(msg)

            rule_found_and_processed = False

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
                    print(
                        f"  Найдено соответствие правилу (URL: {rule.action.url}). Выполняем..."
                    )

                    attachments = None
                    if rule.attachment_field:
                        attachments = EmailParser.get_attachments(msg)

                    success, url, error = await apply_rule_action(
                        rule, body, subject, sender, attachments
                    )
                    if success:
                        print("  Действие выполнено успешно. Помечаем как прочитанное.")
                        client.mark_as_seen(mail_id)
                    else:
                        print(
                            f"  [ОШИБКА] Действие для URL {url} не выполнено: {error}"
                        )
                        print(
                            "  Письмо не будет отмечено как прочитанное из-за ошибки."
                        )

                    rule_found_and_processed = True
                    break

            if not rule_found_and_processed:
                print(f"  Письмо от {sender} не соответствует ни одному из правил.")

    except Exception as e:
        print(
            f"[КРИТИЧЕСКАЯ ОШИБКА] Произошла непредвиденная ошибка в работе сервиса: {e}"
        )
    finally:
        client.logout()
