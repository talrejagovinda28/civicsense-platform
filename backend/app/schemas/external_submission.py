import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.external_submission import ExternalSubmissionStatus


class ExternalSubmissionResponse(BaseModel):
    id: uuid.UUID
    complaint_id: uuid.UUID
    routing_channel_id: uuid.UUID | None
    provider: str
    status: ExternalSubmissionStatus
    external_token: str | None
    status_url: str | None
    forwarded_at: datetime | None
    token_received_at: datetime | None
    reference_note: str | None = None

    model_config = {"from_attributes": True}


class ExternalSubmissionStartRequest(BaseModel):
    routing_channel_id: uuid.UUID | None = None


class ExternalSubmissionTokenRequest(BaseModel):
    external_token: str = Field(min_length=3, max_length=120)
    status_url: str | None = Field(default=None, max_length=500)
