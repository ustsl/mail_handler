from pydantic import BaseModel


class MailCheckSettings(BaseModel):
    imap_server: str
    imap_port: int
    username: str
    password: str
