from src.processors.common_insurance import common_insurance_rule
from src.processors.insurance_rules.sogaz_insurance_rule import sogaz_insurance_rule
from src.processors.insurance_rules.renins_insurance_rule import renins_insurance_rule
from src.processors.insurance_rules.ingos_insurance_rule import (
    ingosstrah_insurance_rule,
)
from src.processors.insurance_rules.alfa_insurance_rule import alfa_insurance_rule
from src.processors.insurance_rules.vsk_insurance_rule import vsk_insurance_rule
from src.processors.insurance_rules.sovcom_insurance_rule import sovcom_insurance_rule
from src.processors.insurance_rules.rgs_insurance_rule import rgs_insurance_rule
from src.processors.insurance_rules.reso_insurance_rule import reso_insurance_rule
from src.processors.insurance_rules.luchi_insurance_rule import luchi_insurance_rule

from src.query_worker.schema import QueryRules
from src.settings import INSURANCE_QUERY_TYPE, INSURANCE_URL, insurance_headers


rules = [
    {
        "rule": {
            "sender": "@imvo.site",
        },
        "action": {
            "type": INSURANCE_QUERY_TYPE,
            "url": f"{INSURANCE_URL}",
            "headers": insurance_headers,
            "processor": luchi_insurance_rule,
        },
        "attachment_field": True,
    },
    {
        "rule": {
            "sender": "@sogaz.ru",
        },
        "action": {
            "type": INSURANCE_QUERY_TYPE,
            "url": INSURANCE_URL,
            "headers": insurance_headers,
            "processor": sogaz_insurance_rule,
        },
        "attachment_field": True,
    },
    {
        "rule": {
            "sender": "@alfastrah.ru",
        },
        "action": {
            "type": INSURANCE_QUERY_TYPE,
            "url": INSURANCE_URL,
            "headers": insurance_headers,
            "processor": alfa_insurance_rule,
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
            "processor": common_insurance_rule,
        },
        "attachment_field": True,
    },
    {
        "rule": {
            "sender": "@ingos.ru",
        },
        "action": {
            "type": INSURANCE_QUERY_TYPE,
            "url": INSURANCE_URL,
            "headers": insurance_headers,
            "processor": ingosstrah_insurance_rule,
        },
        "attachment_field": True,
    },
    {
        "rule": {
            "sender": "@vsk.ru",
        },
        "action": {
            "type": INSURANCE_QUERY_TYPE,
            "url": INSURANCE_URL,
            "headers": insurance_headers,
            "processor": vsk_insurance_rule,
        },
        "attachment_field": True,
    },
    {
        "rule": {
            "sender": "@sovcomins.ru",
        },
        "action": {
            "type": INSURANCE_QUERY_TYPE,
            "url": INSURANCE_URL,
            "headers": insurance_headers,
            "processor": sovcom_insurance_rule,
        },
        "attachment_field": True,
    },
    {
        "rule": {
            "sender": "@rgs.ru",
        },
        "action": {
            "type": INSURANCE_QUERY_TYPE,
            "url": INSURANCE_URL,
            "headers": insurance_headers,
            "processor": rgs_insurance_rule,
        },
        "attachment_field": True,
    },
    {
        "rule": {
            "sender": "@absolutins.ru",
        },
        "action": {
            "type": INSURANCE_QUERY_TYPE,
            "url": INSURANCE_URL,
            "headers": insurance_headers,
            "processor": common_insurance_rule,
        },
        "attachment_field": True,
    },
    {
        "rule": {
            "sender": "@luchi.ru",
        },
        "action": {
            "type": INSURANCE_QUERY_TYPE,
            "url": INSURANCE_URL,
            "headers": insurance_headers,
            "processor": luchi_insurance_rule,
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
            "processor": common_insurance_rule,
        },
        "attachment_field": True,
    },
    {
        "rule": {
            "sender": "@zettains.ru",
        },
        "action": {
            "type": INSURANCE_QUERY_TYPE,
            "url": INSURANCE_URL,
            "headers": insurance_headers,
            "processor": common_insurance_rule,
        },
        "attachment_field": True,
    },
    {
        "rule": {
            "sender": "@reso.ru",
        },
        "action": {
            "type": INSURANCE_QUERY_TYPE,
            "url": INSURANCE_URL,
            "headers": insurance_headers,
            "processor": reso_insurance_rule,
        },
        "attachment_field": True,
    },
    {
        "rule": {
            "sender": "@renins.com",
        },
        "action": {
            "type": INSURANCE_QUERY_TYPE,
            "url": INSURANCE_URL,
            "headers": insurance_headers,
            "processor": renins_insurance_rule,
        },
        "attachment_field": True,
    },
    {
        "rule": {
            "sender": "@invitro.ru",
        },
        "action": {
            "type": INSURANCE_QUERY_TYPE,
            "url": INSURANCE_URL,
            "headers": insurance_headers,
            "processor": common_insurance_rule,
        },
        "attachment_field": True,
    },
    {
        "rule": {
            "sender": "@ugsk.ru",
        },
        "action": {
            "type": INSURANCE_QUERY_TYPE,
            "url": INSURANCE_URL,
            "headers": insurance_headers,
            "processor": common_insurance_rule,
        },
        "attachment_field": True,
    },
    {
        "rule": {
            "sender": "@crosshub.ru",
        },
        "action": {
            "type": INSURANCE_QUERY_TYPE,
            "url": INSURANCE_URL,
            "headers": insurance_headers,
            "processor": common_insurance_rule,
        },
        "attachment_field": True,
    },
]

rules = QueryRules.model_validate(rules)
