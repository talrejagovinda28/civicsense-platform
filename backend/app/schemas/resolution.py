import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class EvidenceSubmitRequest(BaseModel):
    assertion: str = Field(min_length=1, max_length=2000)
    submitter_role: str = Field(pattern="^(citizen|officer|moderator)$")
    media_url: str | None = None


class EvidenceResponse(BaseModel):
    id: uuid.UUID
    complaint_id: uuid.UUID
    submitter_id: str
    submitter_role: str
    assertion: str
    status: str
    created_at: datetime

    model_config = {"from_attributes": True}


class ReporterConfirmRequest(BaseModel):
    confirmed: bool
    reason: str | None = None


class IndependentReviewRequest(BaseModel):
    evidence_id: uuid.UUID | None = None
    decision: str = Field(min_length=1, max_length=50)
    reason: str | None = None


class VerificationResponse(BaseModel):
    id: uuid.UUID
    verification_state: str

    model_config = {"from_attributes": True}


class ReviewResponse(BaseModel):
    id: uuid.UUID
    complaint_id: uuid.UUID
    evidence_id: uuid.UUID | None
    decision: str
    reviewer_id: str
    created_at: datetime

    model_config = {"from_attributes": True}
