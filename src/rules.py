### RULES FOR WORKING WITH LETTERS


from src.processors.prodoctorov import prodoctorov_parse_email
from src.processors.sber import sber_parse_email
from src.query_worker.schema import QueryRules
from src.settings import CLIENT_EMAIL, CRM_QUERY_TYPE, CRM_URL, crm_headers

"""
Consists of two parts: rule, action.

The rules describe: 
- the sender and/or the match with part of the subject of the letter

The actions describe:
- the post-request rule,
- connect the letter processor (which, by agreement, should be placed in the processors folder)
"""

rules = [
    {
        "rule": {"sender": "info@medflex.ru", "subject": "запись"},
        "action": {
            "type": CRM_QUERY_TYPE,
            "url": CRM_URL,
            "headers": crm_headers,
            "processor": prodoctorov_parse_email,
        },
    },
    {
        "rule": {"sender": "clinic-online@sberhealth.ru", "subject": "СберЗдоровье"},
        "action": {
            "type": CRM_QUERY_TYPE,
            "url": CRM_URL,
            "headers": crm_headers,
            "processor": sber_parse_email,
        },
    },
    {
        "rule": {"sender": "info@smt-clinic.ru", "subject": "СберЗдоровье"},
        "action": {
            "type": CRM_QUERY_TYPE,
            "url": CRM_URL,
            "headers": crm_headers,
            "processor": sber_parse_email,
        },
    },
]

rules = QueryRules.model_validate(rules)
