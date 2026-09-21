from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Any, Protocol, TypedDict


class OutcomeState(StrEnum):
    NOT_SENT = "not_sent"
    USER_ACTION_REQUIRED = "user_action_required"
    PROVIDER_ACCEPTED = "provider_accepted"
    ACKNOWLEDGED = "acknowledged"
    OFFICIALLY_REGISTERED = "officially_registered"
    REJECTED = "rejected"
    UNKNOWN_OUTCOME = "unknown_outcome"


class IntentPayload(TypedDict, total=False):
    complaint_id: str
    payload_hash: str
    destination: str
    scenario: str
    disclosure: dict[str, Any]


@dataclass(frozen=True)
class EligibilityResult:
    eligible: bool
    reason: str | None = None
    missing_fields: tuple[str, ...] = ()


@dataclass(frozen=True)
class PreparedSubmission:
    payload_hash: str
    destination: str
    transport_metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(frozen=True)
class SubmissionOutcome:
    state: OutcomeState
    message: str
    provider_message_id: str | None = None
    official_reference: str | None = None
    tracking_url: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


class SubmissionAdapter(Protocol):
    def validate(self, intent: IntentPayload) -> EligibilityResult: ...

    def prepare(self, intent: IntentPayload) -> PreparedSubmission: ...

    def submit(self, intent: IntentPayload, *, idempotency_key: str) -> SubmissionOutcome: ...

    def reconcile(self, intent: IntentPayload) -> SubmissionOutcome: ...
