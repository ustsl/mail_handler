from email.header import decode_header
from email.utils import parseaddr


class EmailParser:
    """EMAIL PARSER WORKER"""

    @staticmethod
    def decode_subject(subject_raw):
        subject, encoding = decode_header(subject_raw)[0]
        if isinstance(subject, bytes):
            subject = subject.decode(encoding if encoding else "utf-8")
        return subject

    @staticmethod
    def decode_sender(sender_raw):
        name, email_addr = parseaddr(sender_raw)
        return email_addr

    @staticmethod
    def get_body(msg):
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
                        body_text = body.decode("utf-8", errors="ignore")
                        break
        else:
            body = msg.get_payload(decode=True)
            if body:
                body_text = body.decode("utf-8", errors="ignore")
        return body_text
