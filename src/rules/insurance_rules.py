### RULES FOR WORKING WITH LETTERS

from src.processors.test import test_rule
from src.query_worker.schema import QueryRules
from src.settings import INSURANCE_QUERY_TYPE, INSURANCE_URL, insurance_headers

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
        "rule": {
            "sender": "work@imvo.site",
        },
        "action": {
            "type": INSURANCE_QUERY_TYPE,
            "url": INSURANCE_URL,
            "headers": insurance_headers,
            "processor": test_rule,
        },
        "attachment_field": True,
    },
    {
        "rule": {
            "sender": "66_sogl@sogaz.ru",
        },
        "action": {
            "type": INSURANCE_QUERY_TYPE,
            "url": INSURANCE_URL,
            "headers": insurance_headers,
            "processor": test_rule,
        },
        "attachment_field": True,
    },
    {
        "rule": {
            "sender": "avis@alfastrah.ru",
        },
        "action": {
            "type": INSURANCE_QUERY_TYPE,
            "url": INSURANCE_URL,
            "headers": insurance_headers,
            "processor": test_rule,
        },
        "attachment_field": True,
    },
    {
        "rule": {
            "sender": "borisovaks94@mail.ru",
        },
        "action": {
            "type": INSURANCE_QUERY_TYPE,
            "url": INSURANCE_URL,
            "headers": insurance_headers,
            "processor": test_rule,
        },
        "attachment_field": True,
    },
    {
        "rule": {
            "sender": "calc@ingos.ru",
        },
        "action": {
            "type": INSURANCE_QUERY_TYPE,
            "url": INSURANCE_URL,
            "headers": insurance_headers,
            "processor": test_rule,
        },
        "attachment_field": True,
    },
    {
        "rule": {
            "sender": "Divanyan@VSK.RU",
        },
        "action": {
            "type": INSURANCE_QUERY_TYPE,
            "url": INSURANCE_URL,
            "headers": insurance_headers,
            "processor": test_rule,
        },
        "attachment_field": True,
    },
    {
        "rule": {
            "sender": "dms_msk@sovcomins.ru",
        },
        "action": {
            "type": INSURANCE_QUERY_TYPE,
            "url": INSURANCE_URL,
            "headers": insurance_headers,
            "processor": test_rule,
        },
        "attachment_field": True,
    },
    {
        "rule": {
            "sender": "dmsvsk1@vsk.ru",
        },
        "action": {
            "type": INSURANCE_QUERY_TYPE,
            "url": INSURANCE_URL,
            "headers": insurance_headers,
            "processor": test_rule,
        },
        "attachment_field": True,
    },
    {
        "rule": {
            "sender": "EkaterinburgDMS@alfastrah.ru",
        },
        "action": {
            "type": INSURANCE_QUERY_TYPE,
            "url": INSURANCE_URL,
            "headers": insurance_headers,
            "processor": test_rule,
        },
        "attachment_field": True,
    },
    {
        "rule": {
            "sender": "ek_fomln@reso.ru",
        },
        "action": {
            "type": INSURANCE_QUERY_TYPE,
            "url": INSURANCE_URL,
            "headers": insurance_headers,
            "processor": test_rule,
        },
        "attachment_field": True,
    },
    {
        "rule": {
            "sender": "garant@rgs.ru",
        },
        "action": {
            "type": INSURANCE_QUERY_TYPE,
            "url": INSURANCE_URL,
            "headers": insurance_headers,
            "processor": test_rule,
        },
        "attachment_field": True,
    },
    {
        "rule": {
            "sender": "GP@renins.com",
        },
        "action": {
            "type": INSURANCE_QUERY_TYPE,
            "url": INSURANCE_URL,
            "headers": insurance_headers,
            "processor": test_rule,
        },
        "attachment_field": True,
    },
    {
        "rule": {
            "sender": "info@smt-clinic.ru",
        },
        "action": {
            "type": INSURANCE_QUERY_TYPE,
            "url": INSURANCE_URL,
            "headers": insurance_headers,
            "processor": test_rule,
        },
        "attachment_field": True,
    },
    {
        "rule": {
            "sender": "lpu@ingos.ru",
        },
        "action": {
            "type": INSURANCE_QUERY_TYPE,
            "url": INSURANCE_URL,
            "headers": insurance_headers,
            "processor": test_rule,
        },
        "attachment_field": True,
    },
    {
        "rule": {
            "sender": "marketing@medrabotnik.online",
        },
        "action": {
            "type": INSURANCE_QUERY_TYPE,
            "url": INSURANCE_URL,
            "headers": insurance_headers,
            "processor": test_rule,
        },
        "attachment_field": True,
    },
    {
        "rule": {
            "sender": "med@absolutins.ru",
        },
        "action": {
            "type": INSURANCE_QUERY_TYPE,
            "url": INSURANCE_URL,
            "headers": insurance_headers,
            "processor": test_rule,
        },
        "attachment_field": True,
    },
    {
        "rule": {
            "sender": "med@luchi.ru",
        },
        "action": {
            "type": INSURANCE_QUERY_TYPE,
            "url": INSURANCE_URL,
            "headers": insurance_headers,
            "processor": test_rule,
        },
        "attachment_field": True,
    },
    {
        "rule": {
            "sender": "medpult@sogaz.ru",
        },
        "action": {
            "type": INSURANCE_QUERY_TYPE,
            "url": INSURANCE_URL,
            "headers": insurance_headers,
            "processor": test_rule,
        },
        "attachment_field": True,
    },
    {
        "rule": {
            "sender": "06medpult@sogaz.ru",
        },
        "action": {
            "type": INSURANCE_QUERY_TYPE,
            "url": INSURANCE_URL,
            "headers": insurance_headers,
            "processor": test_rule,
        },
        "attachment_field": True,
    },
    {
        "rule": {
            "sender": "13medpult@sogaz.ru",
        },
        "action": {
            "type": INSURANCE_QUERY_TYPE,
            "url": INSURANCE_URL,
            "headers": insurance_headers,
            "processor": test_rule,
        },
        "attachment_field": True,
    },
    {
        "rule": {
            "sender": "mural@reso.ru",
        },
        "action": {
            "type": INSURANCE_QUERY_TYPE,
            "url": INSURANCE_URL,
            "headers": insurance_headers,
            "processor": test_rule,
        },
        "attachment_field": True,
    },
    {
        "rule": {
            "sender": "mytask@renins.com",
        },
        "action": {
            "type": INSURANCE_QUERY_TYPE,
            "url": INSURANCE_URL,
            "headers": insurance_headers,
            "processor": test_rule,
        },
        "attachment_field": True,
    },
    {
        "rule": {
            "sender": "oprotono@gmail.com",
        },
        "action": {
            "type": INSURANCE_QUERY_TYPE,
            "url": INSURANCE_URL,
            "headers": insurance_headers,
            "processor": test_rule,
        },
        "attachment_field": True,
    },
    {
        "rule": {
            "sender": "pulse.letter@zettains.ru",
        },
        "action": {
            "type": INSURANCE_QUERY_TYPE,
            "url": INSURANCE_URL,
            "headers": insurance_headers,
            "processor": test_rule,
        },
        "attachment_field": True,
    },
    {
        "rule": {
            "sender": "regdoctor@reso.ru",
        },
        "action": {
            "type": INSURANCE_QUERY_TYPE,
            "url": INSURANCE_URL,
            "headers": insurance_headers,
            "processor": test_rule,
        },
        "attachment_field": True,
    },
    {
        "rule": {
            "sender": "robotlpu@sogaz.ru",
        },
        "action": {
            "type": INSURANCE_QUERY_TYPE,
            "url": INSURANCE_URL,
            "headers": insurance_headers,
            "processor": test_rule,
        },
        "attachment_field": True,
    },
    {
        "rule": {
            "sender": "smtclinic@smt-clinic.ru",
        },
        "action": {
            "type": INSURANCE_QUERY_TYPE,
            "url": INSURANCE_URL,
            "headers": insurance_headers,
            "processor": test_rule,
        },
        "attachment_field": True,
    },
    {
        "rule": {
            "sender": "Soglasovmed@renins.com",
        },
        "action": {
            "type": INSURANCE_QUERY_TYPE,
            "url": INSURANCE_URL,
            "headers": insurance_headers,
            "processor": test_rule,
        },
        "attachment_field": True,
    },
    {
        "rule": {
            "sender": "SpiskiLPU@renins.com",
        },
        "action": {
            "type": INSURANCE_QUERY_TYPE,
            "url": INSURANCE_URL,
            "headers": insurance_headers,
            "processor": test_rule,
        },
        "attachment_field": True,
    },
    {
        "rule": {
            "sender": "srs@invitro.ru",
        },
        "action": {
            "type": INSURANCE_QUERY_TYPE,
            "url": INSURANCE_URL,
            "headers": insurance_headers,
            "processor": test_rule,
        },
        "attachment_field": True,
    },
    {
        "rule": {
            "sender": "254-mail-dms@ugsk.ru",
        },
        "action": {
            "type": INSURANCE_QUERY_TYPE,
            "url": INSURANCE_URL,
            "headers": insurance_headers,
            "processor": test_rule,
        },
        "attachment_field": True,
    },
]

rules = QueryRules.model_validate(rules)
