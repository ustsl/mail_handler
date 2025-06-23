### RULES FOR WORKING WITH LETTERS


from src.processors.prodoctorov import prodoctorov_parse_email
from src.processors.sber import sber_parse_email
from src.processors.test import test_rule
from src.query_worker.schema import QueryRules
from src.settings import CRM_QUERY_TYPE, CRM_URL, crm_headers

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
        "rule": {"sender": "work@imvo.site",},
        "action": {
            "type": CRM_QUERY_TYPE,
            "url": CRM_URL,
            "headers": crm_headers,
            "processor": test_rule,
        },
        "attachment_field": "file"
    },
]

rules = QueryRules.model_validate(rules)
