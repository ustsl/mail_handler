from email.header import decode_header
from email.utils import parseaddr


class EmailParser:
    """EMAIL PARSER WORKER"""

    @staticmethod
    def decode_subject(subject_raw):
        decoded_parts = decode_header(subject_raw)
        subject, encoding = decoded_parts[0]

        if encoding is None or encoding.lower() == "unknown-8bit":
            encoding = "utf-8"
        if isinstance(subject, bytes):
            subject = subject.decode(encoding, errors="replace")
        return subject

    @staticmethod
    def decode_sender(sender_raw):
        name, email_addr = parseaddr(sender_raw)
        return email_addr

    @staticmethod
    def decode_bytes(payload):
        """
        Tries to decode the byte string using several encodings.
        """
        encodings = ["utf-8", "cp1251", "iso-8859-1"]
        for enc in encodings:
            try:
                return payload.decode(enc)
            except Exception:
                continue
        return payload.decode("utf-8", errors="replace")

    @staticmethod
    def get_body(msg):
        """
        Извлекает тело письма, отдавая приоритет HTML-версии.
        - Если письмо multipart, ищет и 'text/html', и 'text/plain'.
        - Возвращает HTML, если найден, иначе возвращает Plain Text.
        - Корректно обрабатывает одночастные (non-multipart) письма.
        """
        html_body = None
        plain_body = None

        if msg.is_multipart():
            # Проходим по всем частям письма
            for part in msg.walk():
                # Пропускаем вложения и вложенные multipart-части
                if (
                    part.get_content_maintype() == "multipart"
                    or part.get("Content-Disposition") is not None
                ):
                    continue

                # Ищем HTML-часть
                if part.get_content_type() == "text/html":
                    payload = part.get_payload(decode=True)
                    if payload:
                        html_body = EmailParser.decode_bytes(payload)

                # Ищем текстовую часть
                elif part.get_content_type() == "text/plain":
                    payload = part.get_payload(decode=True)
                    if payload:
                        plain_body = EmailParser.decode_bytes(payload)

        else:
            payload = msg.get_payload(decode=True)
            if payload:
                # Предполагаем, что это может быть plain text по умолчанию,
                # но может быть и HTML. В данном контексте это не так критично.
                plain_body = EmailParser.decode_bytes(payload)

        # Отдаем приоритет HTML, так как процессор работает с ним.
        # Если HTML нет, возвращаем plain text.
        return html_body if html_body is not None else plain_body

    @staticmethod
    def get_attachments(msg) -> list[tuple[str, bytes]]:
        """
        Extracts attachments from the email.
        Returns a list of tuples, where each tuple contains (filename, file_data_bytes).
        """
        attachments = []
        for part in msg.walk():
            if (
                part.get_content_maintype() != "multipart"
                and part.get("Content-Disposition") is not None
            ):
                filename = part.get_filename()
                if filename:
                    decoded_filename_parts = decode_header(filename)
                    decoded_filename = []
                    for part_fn, encoding in decoded_filename_parts:
                        if isinstance(part_fn, bytes):
                            encoding = encoding or "utf-8"
                            decoded_filename.append(
                                part_fn.decode(encoding, errors="replace")
                            )
                        else:
                            decoded_filename.append(part_fn)

                    final_filename = "".join(decoded_filename)
                    file_data = part.get_payload(decode=True)
                    attachments.append((final_filename, file_data))
        return attachments
