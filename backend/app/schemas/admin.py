from typing import Literal

from pydantic import BaseModel


class CountItem(BaseModel):
    label: str
    count: int


class AdminStatsResponse(BaseModel):
    city: str
    total: int
    by_status: list[CountItem]
    by_category: list[CountItem]


class RoleUpdateRequest(BaseModel):
    role: Literal["citizen", "officer", "admin"]


class RoleUpdateResponse(BaseModel):
    user_id: str
    role: str
