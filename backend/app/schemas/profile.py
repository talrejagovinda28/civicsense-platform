import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ProfileUpdateRequest(BaseModel):
    display_name: str | None = Field(default=None, max_length=200)
    bio: str | None = Field(default=None, max_length=1000)
    is_private: bool | None = None
    dm_policy: str | None = None


class ProfileResponse(BaseModel):
    id: uuid.UUID
    user_id: str
    handle: str
    display_name: str | None
    bio: str | None = None
    is_private: bool = False
    dm_policy: str = "requests"
    created_at: datetime

    model_config = {"from_attributes": True}


class ReputationResponse(BaseModel):
    lifetime_xp: int
    can_initiate_dm: bool
    can_create_group: bool
    badges: list[str] = Field(default_factory=list)
