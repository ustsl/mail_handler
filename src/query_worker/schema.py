from enum import Enum
from typing import Callable, List, Optional

from pydantic import BaseModel, RootModel, model_validator


class HTTPMethod(str, Enum):
    GET = "GET"
    POST = "POST"
    PUT = "PUT"
    PATCH = "PATCH"
    DELETE = "DELETE"
    OPTIONS = "OPTIONS"
    HEAD = "HEAD"


class Condition(BaseModel):
    sender: Optional[str] = None
    subject: Optional[str] = None

    @model_validator(mode="after")
    def check_at_least_one(cls, values: "Condition") -> "Condition":
        if values.sender is None and values.subject is None:
            raise ValueError(
                "Хотя бы одно из полей 'sender' или 'subject' должно быть указано."
            )
        return values


class Action(BaseModel):
    type: HTTPMethod
    url: str
    headers: dict
    processor: Optional[Callable] = None


class Rule(BaseModel):
    name: Optional[str] = None
    rule: Condition
    action: Action
    attachment_field: Optional[bool] = None
    permanent_file: bool = False


class QueryRules(RootModel[List[Rule]]):
    pass
