import email
import imaplib

from src.email_worker.schema import MailCheckSettings


class MailClient:
    """IMAP SERVER WORKER"""

    def __init__(self, settings: MailCheckSettings):
        self.settings = settings
        self.connection = None

    def connect(self):
        self.connection = imaplib.IMAP4_SSL(
            self.settings.imap_server, self.settings.imap_port
        )
        self.connection.login(self.settings.username, self.settings.password)
        self.connection.select("inbox")

    def search_unseen(self):
        status, messages = self.connection.search(None, "UNSEEN")
        mail_ids = messages[0].split() if messages and messages[0] else []
        return mail_ids

    def fetch_email(self, mail_id):
        status, msg_data = self.connection.fetch(mail_id, "(RFC822)")
        raw_email = msg_data[0][1]
        return email.message_from_bytes(raw_email)

    def mark_as_seen(self, mail_id):
        self.connection.store(mail_id, "+FLAGS", "\\Seen")

    def logout(self):
        if self.connection:
            self.connection.close()
            self.connection.logout()
            self.connection = None
