import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class CommentCreateRequest(BaseModel):
    body: str = Field(min_length=1, max_length=2000)


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
