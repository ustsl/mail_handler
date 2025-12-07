from src.processors.insurance_rules.renins_pult_insurance_rule import (
    renins_pult_insurance_rule,
)
from src.processors.common_insurance import common_insurance_rule
from src.processors.insurance_rules.akbars_insurance_rule import akbars_insurance_rule
from src.processors.insurance_rules.alfa_insurance_rule import alfa_insurance_rule
from src.processors.insurance_rules.energogarant_insurance_rule import (
    energogarant_insurance_rule,
)
from src.processors.insurance_rules.ingos_insurance_rule import (
    ingosstrah_insurance_rule,
)
from src.processors.insurance_rules.luchi_insurance_rule import luchi_insurance_rule
from src.processors.insurance_rules.renins_insurance_rule import renins_insurance_rule
from src.processors.insurance_rules.reso_insurance_rule import reso_insurance_rule
from src.processors.insurance_rules.rgs_insurance_rule import rgs_insurance_rule
from src.processors.insurance_rules.sber_insurance_rule import (
    sber_digital_assistant_insurance_rule,
    sber_ins_insurance_rule,
    sber_insurance_rule,
)
from src.processors.insurance_rules.sogaz_insurance_rule import sogaz_insurance_rule
from src.processors.insurance_rules.sovcom_insurance_rule import sovcom_insurance_rule
from src.processors.insurance_rules.ugsk_insurance_rule import ugsk_insurance_rule
from src.processors.insurance_rules.vsk_insurance_rule import vsk_insurance_rule
from src.processors.insurance_rules.zetta_insurance_rule import (
    zetta_insurance_rule,
    zetta_pulse_insurance_rule,
)
from src.query_worker.schema import QueryRules
from src.settings import INSURANCE_QUERY_TYPE, INSURANCE_URL, insurance_headers

rules = [
    {
        "name": "insurance_imvo_renins_pult",
        "rule": {
            "sender": "@imvo.site",
        },
        "action": {
            "type": INSURANCE_QUERY_TYPE,
            "url": f"{INSURANCE_URL}",
            "headers": insurance_headers,
            "processor": sber_digital_assistant_insurance_rule,
        },
        "attachment_field": True,
    },
    {
        "name": "insurance_renins_pult",
        "rule": {
            "sender": "@mldc-nt.ru",
        },
        "action": {
            "type": INSURANCE_QUERY_TYPE,
            "url": f"{INSURANCE_URL}",
            "headers": insurance_headers,
            "processor": renins_pult_insurance_rule,
        },
        "attachment_field": True,
    },
    {
        "name": "insurance_energogarant",
        "rule": {
            "sender": "@energogarant.ru",
        },
        "action": {
            "type": INSURANCE_QUERY_TYPE,
            "url": f"{INSURANCE_URL}",
            "headers": insurance_headers,
            "processor": energogarant_insurance_rule,
        },
        "attachment_field": True,
    },
    {
        "name": "insurance_sogaz",
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
        "permanent_file": True,
    },
    {
        "name": "insurance_alfastrah",
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
        "name": "insurance_borisovaks",
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
        "name": "insurance_ingos",
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
        "name": "insurance_vsk",
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
        "name": "insurance_sovcom",
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
        "name": "insurance_rgs",
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
        "name": "insurance_absolut",
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
        "name": "insurance_luchi",
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
        "name": "insurance_oprotono",
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
        "name": "insurance_zetta_pulse",
        "rule": {
            "sender": "pulse.letter@zettains.ru",
        },
        "action": {
            "type": INSURANCE_QUERY_TYPE,
            "url": INSURANCE_URL,
            "headers": insurance_headers,
            "processor": zetta_pulse_insurance_rule,
        },
        "attachment_field": True,
    },
    {
        "name": "insurance_zetta",
        "rule": {
            "sender": "@zettains.ru",
        },
        "action": {
            "type": INSURANCE_QUERY_TYPE,
            "url": INSURANCE_URL,
            "headers": insurance_headers,
            "processor": zetta_insurance_rule,
        },
        "attachment_field": True,
    },
    {
        "name": "insurance_reso",
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
        "name": "insurance_renins",
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
        "name": "insurance_invitro",
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
        "name": "insurance_ugsk",
        "rule": {
            "sender": "@ugsk.ru",
        },
        "action": {
            "type": INSURANCE_QUERY_TYPE,
            "url": INSURANCE_URL,
            "headers": insurance_headers,
            "processor": ugsk_insurance_rule,
        },
        "attachment_field": True,
    },
    {
        "name": "insurance_crosshub",
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
    {
        "name": "insurance_sberhealth",
        "rule": {
            "sender": "@sberhealth.ru",
        },
        "action": {
            "type": INSURANCE_QUERY_TYPE,
            "url": INSURANCE_URL,
            "headers": insurance_headers,
            "processor": sber_insurance_rule,
        },
        "attachment_field": True,
    },
    {
        "name": "insurance_sberins_digital_assistant",
        "rule": {
            "sender": "digital.assistant@sberins.ru",
        },
        "action": {
            "type": INSURANCE_QUERY_TYPE,
            "url": INSURANCE_URL,
            "headers": insurance_headers,
            "processor": sber_digital_assistant_insurance_rule,
        },
        "attachment_field": True,
    },
    {
        "name": "insurance_sberins",
        "rule": {"sender": "@sberins.ru"},
        "action": {
            "type": INSURANCE_QUERY_TYPE,
            "url": INSURANCE_URL,
            "headers": insurance_headers,
            "processor": sber_ins_insurance_rule,
        },
        "attachment_field": True,
    },
    {
        "name": "insurance_akbars",
        "rule": {
            "sender": "@akbarsmed.ru",
        },
        "action": {
            "type": INSURANCE_QUERY_TYPE,
            "url": f"{INSURANCE_URL}",
            "headers": insurance_headers,
            "processor": akbars_insurance_rule,
        },
        "attachment_field": True,
    },
]

rules = QueryRules.model_validate(rules)
