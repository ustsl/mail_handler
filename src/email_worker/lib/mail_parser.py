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
        Extracts the body of the email:
          - If the email is multipart, finds the first text part without an attachment.
          - If not multipart, tries to decode the payload.
          - Uses decode_bytes to try several decoding options.
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
