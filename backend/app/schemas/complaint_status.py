import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.complaint import ComplaintStatus


class StatusHistoryResponse(BaseModel):
    id: uuid.UUID
    status: ComplaintStatus
    note: str | None
    updated_by: str
    created_at: datetime

    model_config = {"from_attributes": True}


class StatusUpdateRequest(BaseModel):
    status: ComplaintStatus
    note: str | None = Field(default=None, max_length=2000)
