"""
Response Models for the API
"""

import dataclasses
from typing import Any, Dict, List, Optional, Union

import flask
from typing_extensions import Literal


@dataclasses.dataclass
class UserObject:
    pass


DataObject = Union[UserObject, Dict[str, Any]]


@dataclasses.dataclass
class BaseResponse:
    status: Literal["ok", "error"]


@dataclasses.dataclass
class OkResponse(BaseResponse):
    data: DataObject


@dataclasses.dataclass
class ErrorResponse(BaseResponse):
    error: Union[Any, List[Dict[Literal["code", "message"], str]]]

