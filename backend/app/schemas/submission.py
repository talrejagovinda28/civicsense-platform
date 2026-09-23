import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field


class ConsentCreateRequest(BaseModel):
    channel_id: uuid.UUID
    disclosure_json: dict[str, Any]
    scope: str = "single_dispatch"


class ConsentResponse(BaseModel):
    id: uuid.UUID
    complaint_id: uuid.UUID
    channel_id: uuid.UUID
    payload_hash: str
    authorized_at: datetime

    model_config = {"from_attributes": True}


class DispatchRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    consent_id: uuid.UUID
    idempotency_key: str = Field(min_length=8, max_length=128)


class DispatchResponse(BaseModel):
    intent_id: uuid.UUID | None = None
    status: str
    outcome_state: str | None = None
    message: str | None = None
    provider_message_id: str | None = None
    official_reference: str | None = None
    metadata: dict[str, Any] | None = None
    unknown_outcome: bool | None = None
    attempt_no: int | None = None
    idempotent_replay: bool | None = None
    code: str | None = None


class AttestSentRequest(BaseModel):
    attestation_note: str | None = None


class AttachReferenceRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    reference_value: str = Field(min_length=1, max_length=200)
    tracking_url: str | None = None


class SubmissionChannelSummary(BaseModel):
    id: uuid.UUID
    label: str
    channel_type: str
    mode: str
    enabled: bool
    url: str | None = None


class ReconcileRequest(BaseModel):
    determination: str = Field(pattern="^(sent|not_sent)$")


class VerifyReferenceRequest(BaseModel):
    reference_id: uuid.UUID


class ExternalReferenceResponse(BaseModel):
    id: uuid.UUID
    reference_value: str
    reference_type: str
    tracking_url: str | None
    verified_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class IntentResponse(BaseModel):
    id: uuid.UUID
    complaint_id: uuid.UUID
    status: str
    idempotency_key: str
    created_at: datetime

    model_config = {"from_attributes": True}
