import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ReportCreateRequest(BaseModel):
    target_type: str = Field(min_length=1, max_length=50)
    target_id: str = Field(min_length=1, max_length=255)
    category: str = Field(min_length=1, max_length=50)
    reason: str = Field(min_length=1, max_length=2000)


class ReportResponse(BaseModel):
    id: uuid.UUID
    target_type: str
    target_id: str
    category: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ModerationActionRequest(BaseModel):
    action: str = Field(min_length=1, max_length=50)
    reason: str | None = None


class ModerationActionResponse(BaseModel):
    id: uuid.UUID
    target_type: str
    target_id: str
    action: str
    created_at: datetime

    model_config = {"from_attributes": True}
