from django.views.generic import detail
from ninja import Schema
from typing import Optional, Any, Union, List, Dict
from datetime import datetime
from pydantic import field_validator, model_validator
import json  # 操！这次绝不能漏！

from pydantic import Field


class SuccessSendIPSchema(Schema):  # 定義 TargetSchema 類別
    ips: List[str] = Field(..., description="IP 列表", min_length=1, max_length=10)


class SuccessSendSubdomainSchema(Schema):  # 定義 TargetSchema 類別
    subdomains: List[str] = Field(
        ..., description="子域名列表", min_length=1, max_length=10
    )


class SuccessSendURLSchema(Schema):  # 定義 TargetSchema 類別
    urls: List[str] = Field(..., description="URL 列表", min_length=1, max_length=5)


class SuccessSendToAISchema(Schema):  # 定義 TargetSchema 類別
    detail: str
