import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class TimelineEventResponse(BaseModel):
    id: uuid.UUID
    event_type: str
    actor_kind: str
    authenticity_level: str
    public_payload: dict[str, Any] | None = None
    created_at: datetime


class TimelineListResponse(BaseModel):
    items: list[TimelineEventResponse] = Field(default_factory=list)
