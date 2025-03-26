import os
from dotenv import load_dotenv

from src.email_worker.schema import MailCheckSettings


load_dotenv()


### MAIL SERVER INTEGRATION SECTION

IMAP_SERVER = os.getenv("IMAP_SERVER")
IMAP_PORT = int(os.getenv("IMAP_PORT"))
USERNAME = os.getenv("USERNAME")
PASSWORD = os.getenv("PASSWORD")

mail_settings = MailCheckSettings(
    imap_server=IMAP_SERVER, imap_port=IMAP_PORT, username=USERNAME, password=PASSWORD
)


### CRM INTEGRATION SECTION

CRM_URL = os.getenv("CRM_URL")
CRM_QUERY_TYPE = os.getenv("CRM_QUERY_TYPE")
CRM_TOKEN = os.getenv("CRM_TOKEN")

crm_headers = {"Authorization": CRM_TOKEN}

### OTHER

CLIENT_EMAIL = os.getenv("CLIENT_EMAIL")
