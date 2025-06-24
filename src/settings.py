import os

from dotenv import load_dotenv

from src.email_worker.schema import MailCheckSettings

load_dotenv()

### MAIL SERVER INTEGRATION SECTION

APPOINTMENT_IMAP_SERVER = os.getenv("APPOINTMENT_IMAP_SERVER")
APPOINTMENT_IMAP_PORT = int(os.getenv("APPOINTMENT_IMAP_PORT"))
APPOINTMENT_USERNAME = os.getenv("APPOINTMENT_USERNAME")
APPOINTMENT_PASSWORD = os.getenv("APPOINTMENT_PASSWORD")

appointment_mail_settings = MailCheckSettings(
    imap_server=APPOINTMENT_IMAP_SERVER,
    imap_port=APPOINTMENT_IMAP_PORT,
    username=APPOINTMENT_USERNAME,
    password=APPOINTMENT_PASSWORD,
)

INSURANCE_IMAP_SERVER = os.getenv("INSURANCE_IMAP_SERVER")
INSURANCE_IMAP_PORT = int(os.getenv("INSURANCE_IMAP_PORT"))
INSURANCE_USERNAME = os.getenv("INSURANCE_USERNAME")
INSURANCE_PASSWORD = os.getenv("INSURANCE_PASSWORD")

insurance_mail_settings = MailCheckSettings(
    imap_server=INSURANCE_IMAP_SERVER,
    imap_port=INSURANCE_IMAP_PORT,
    username=INSURANCE_USERNAME,
    password=INSURANCE_PASSWORD,
)

print(appointment_mail_settings, insurance_mail_settings)


### CRM INTEGRATION SECTION

CRM_URL = os.getenv("CRM_URL")
CRM_QUERY_TYPE = os.getenv("CRM_QUERY_TYPE")
CRM_TOKEN = os.getenv("CRM_TOKEN")

crm_headers = {"Authorization": CRM_TOKEN}


INSURANCE_URL = os.getenv("INSURANCE_URL")
INSURANCE_QUERY_TYPE = os.getenv("INSURANCE_QUERY_TYPE")
INSURANCE_TOKEN = os.getenv("INSURANCE_TOKEN")

insurance_headers = {"Authorization": INSURANCE_TOKEN}


### OTHER

CLIENT_EMAIL = os.getenv("CLIENT_EMAIL")
