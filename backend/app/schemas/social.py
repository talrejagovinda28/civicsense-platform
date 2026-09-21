import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class EngagementCounts(BaseModel):
    like_count: int
    affected_count: int
    comment_count: int
    viewer_liked: bool = False
    viewer_affected: bool = False


class CommentCreateRequest(BaseModel):
    body: str = Field(min_length=1, max_length=2000)


class CommentItem(BaseModel):
    id: uuid.UUID
    complaint_id: uuid.UUID
    author_handle: str
    author_display_name: str
    body: str
    is_official: bool = False
    created_at: datetime


class PaginatedComments(BaseModel):
    items: list[CommentItem]
    total: int
    skip: int = Field(ge=0)
    limit: int = Field(ge=1, le=100)


class CommentResponse(BaseModel):
    id: uuid.UUID
    complaint_id: uuid.UUID
    author_id: str
    body: str
    created_at: datetime
    deleted_at: datetime | None = None

    model_config = {"from_attributes": True}


class LikeResponse(BaseModel):
    user_id: str
    complaint_id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class AffectedResponse(BaseModel):
    user_id: str
    complaint_id: uuid.UUID
    created_at: datetime

    model_config = {"from_attributes": True}


class FollowResponse(BaseModel):
    id: uuid.UUID
    follower_id: str
    target_id: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class FollowDecideRequest(BaseModel):
    accept: bool


class BlockResponse(BaseModel):
    id: uuid.UUID
    blocker_id: str
    blocked_id: str
    created_at: datetime

    model_config = {"from_attributes": True}
