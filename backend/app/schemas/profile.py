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
    handle: str
    display_name: str | None = None
    bio: str | None = None
    is_private: bool = False
    follower_count: int = 0
    following_count: int = 0
    viewer_is_following: bool = False
    viewer_follow_pending: bool = False


class OwnProfileResponse(ProfileResponse):
    home_locality: str | None = None


class BadgeItem(BaseModel):
    code: str
    label: str
    granted_at: datetime


class ReputationUnlocks(BaseModel):
    can_initiate_dm: bool
    can_create_groups: bool


class ReputationResponse(BaseModel):
    lifetime_xp: int
    eligible_xp: int
    badges: list[BadgeItem] = Field(default_factory=list)
    unlocks: ReputationUnlocks
