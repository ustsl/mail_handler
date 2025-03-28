from email.header import decode_header
from email.utils import parseaddr


class EmailParser:
    """EMAIL PARSER WORKER"""

    @staticmethod
    def decode_subject(subject_raw):
        subject, encoding = decode_header(subject_raw)[0]
        if isinstance(subject, bytes):
            subject = subject.decode(
                encoding if encoding else "utf-8", errors="replace"
            )
        return subject

    @staticmethod
    def decode_sender(sender_raw):
        name, email_addr = parseaddr(sender_raw)
        return email_addr

    @staticmethod
    def decode_bytes(payload):
        """
        Пытается декодировать байтовую строку с использованием нескольких кодировок.
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
        Извлекает тело письма:
          - Если письмо multipart, ищет первую текстовую часть без вложения
          - Если письмо не multipart, пытается декодировать payload
          - Использует decode_bytes для попытки нескольких вариантов декодирования
        """
        body_text = None
        if msg.is_multipart():
            for part in msg.walk():
                content_type = part.get_content_type()
                content_disposition = str(part.get("Content-Disposition"))
                if (
                    content_type == "text/plain"
                    and "attachment" not in content_disposition
                ):
                    body = part.get_payload(decode=True)
                    if body:
                        body_text = EmailParser.decode_bytes(body)
                        break
        else:
            body = msg.get_payload(decode=True)
            if body:
                body_text = EmailParser.decode_bytes(body)
        return body_text
