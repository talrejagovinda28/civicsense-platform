from __future__ import annotations

import hashlib
import json
import uuid
from datetime import UTC, datetime
from enum import StrEnum

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.models.authority_channel import ChannelActivation, ChannelMode, ExternalChannel
from app.models.complaint import Complaint
from app.models.submission import (
    ComplaintTimelineEvent,
    ExternalReference,
    SubmissionAttempt,
    SubmissionConsent,
    SubmissionIntent,
    TimelineActorKind,
    TimelineAuthenticityLevel,
    TimelineVisibility,
)
from app.services.adapters.base import OutcomeState
from app.services.adapters.registry import ChannelNotEnabled, get_adapter


class IntentStatus(StrEnum):
    CREATED = "created"
    AUTHORIZED = "authorized"
    ATTEMPTING = "attempting"
    USER_ACTION_REQUIRED = "user_action_required"
    PROVIDER_ACCEPTED = "provider_accepted"
    ACK_PENDING = "ack_pending"
    OFFICIALLY_REGISTERED = "officially_registered"
    REJECTED = "rejected"
    UNKNOWN_OUTCOME = "unknown_outcome"
    FAILED = "failed"


def _hash_payload(data: dict) -> str:
    canonical = json.dumps(data, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode()).hexdigest()


def _intent_payload(
    intent: SubmissionIntent,
    consent: SubmissionConsent,
    channel: ExternalChannel,
    *,
    scenario: str | None = None,
) -> dict:
    disclosure = json.loads(consent.disclosure_json)
    url = channel.destination
    if channel.routing_channel is not None and channel.routing_channel.url:
        url = channel.routing_channel.url
    return {
        "complaint_id": str(intent.complaint_id),
        "payload_hash": intent.payload_hash,
        "destination": channel.destination,
        "url": url,
        "disclosure": disclosure,
        "scenario": scenario or intent.test_scenario,
    }


def _outcome_to_intent_status(outcome_state: OutcomeState) -> str:
    mapping = {
        OutcomeState.NOT_SENT: IntentStatus.FAILED,
        OutcomeState.USER_ACTION_REQUIRED: IntentStatus.USER_ACTION_REQUIRED,
        OutcomeState.PROVIDER_ACCEPTED: IntentStatus.PROVIDER_ACCEPTED,
        OutcomeState.ACKNOWLEDGED: IntentStatus.ACK_PENDING,
        OutcomeState.OFFICIALLY_REGISTERED: IntentStatus.OFFICIALLY_REGISTERED,
        OutcomeState.REJECTED: IntentStatus.REJECTED,
        OutcomeState.UNKNOWN_OUTCOME: IntentStatus.UNKNOWN_OUTCOME,
    }
    return mapping.get(outcome_state, IntentStatus.FAILED)


def _append_timeline(
    db: Session,
    *,
    complaint_id: uuid.UUID,
    actor_id: str | None,
    actor_kind: str,
    event_type: str,
    public_payload: dict | None = None,
    idempotency_key: str | None = None,
) -> None:
    db.add(
        ComplaintTimelineEvent(
            complaint_id=complaint_id,
            actor_id=actor_id,
            actor_kind=actor_kind,
            event_type=event_type,
            authenticity_level=TimelineAuthenticityLevel.SYSTEM_DERIVED,
            public_payload_redacted=json.dumps(public_payload) if public_payload else None,
            visibility=TimelineVisibility.OWNER,
            idempotency_key=idempotency_key,
            created_at=datetime.now(UTC),
        )
    )


def create_consent(
    db: Session,
    *,
    user_id: str,
    complaint_id: uuid.UUID,
    channel_id: uuid.UUID,
    disclosure_json: dict,
    scope: str = "single_dispatch",
    version: str = "1",
) -> SubmissionConsent:
    complaint = db.get(Complaint, complaint_id)
    if complaint is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found")
    if complaint.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    channel = db.get(ExternalChannel, channel_id)
    if channel is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Channel not found")

    consent = SubmissionConsent(
        complaint_id=complaint_id,
        user_id=user_id,
        channel_id=channel_id,
        payload_hash=_hash_payload(disclosure_json),
        disclosure_json=json.dumps(disclosure_json),
        version=version,
        authorized_at=datetime.now(UTC),
        scope=scope,
    )
    db.add(consent)
    db.flush()
    _append_timeline(
        db,
        complaint_id=complaint_id,
        actor_id=user_id,
        actor_kind=TimelineActorKind.CITIZEN,
        event_type="submission_consent_created",
        public_payload={"channel_id": str(channel_id)},
    )
    db.commit()
    db.refresh(consent)
    return consent


def create_intent_and_dispatch(
    db: Session,
    *,
    user_id: str,
    complaint_id: uuid.UUID,
    consent_id: uuid.UUID,
    idempotency_key: str,
    test_scenario: str | None = None,
) -> dict:
    complaint = db.get(Complaint, complaint_id)
    if complaint is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Complaint not found")
    if complaint.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    existing = db.scalar(
        select(SubmissionIntent).where(SubmissionIntent.idempotency_key == idempotency_key)
    )
    if existing is not None:
        latest = max(existing.attempts, key=lambda a: a.attempt_no, default=None)
        return {
            "intent_id": existing.id,
            "status": existing.status,
            "idempotent_replay": True,
            "attempt_no": latest.attempt_no if latest else 0,
            "unknown_outcome": latest.unknown_outcome if latest else False,
        }

    consent = db.get(SubmissionConsent, consent_id)
    if consent is None or consent.complaint_id != complaint_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Consent not found")
    if consent.revoked_at is not None:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Consent revoked")

    channel = db.get(ExternalChannel, consent.channel_id)
    if channel is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Channel not found")

    activation = ChannelActivation(channel.activation)
    mode = ChannelMode(channel.mode)
    simulation = activation in {ChannelActivation.TEST_ONLY, ChannelActivation.DISABLED} and (
        test_scenario is not None or activation == ChannelActivation.TEST_ONLY
    )

    if not channel.enabled and not simulation and mode not in {
        ChannelMode.GUIDED_PORTAL,
        ChannelMode.GUIDED_WHATSAPP,
    }:
        return {
            "code": "CHANNEL_NOT_ENABLED",
            "message": "Channel is disabled",
            "status": IntentStatus.FAILED,
        }

    intent = SubmissionIntent(
        complaint_id=complaint_id,
        consent_id=consent_id,
        channel_id=channel.id,
        destination_snapshot=channel.destination,
        payload_hash=consent.payload_hash,
        idempotency_key=idempotency_key,
        status=IntentStatus.AUTHORIZED,
        test_scenario=test_scenario,
    )
    db.add(intent)
    db.flush()

    try:
        adapter = get_adapter(channel, simulation=simulation or test_scenario is not None)
    except ChannelNotEnabled as exc:
        if mode in {ChannelMode.GUIDED_PORTAL, ChannelMode.GUIDED_WHATSAPP}:
            adapter = get_adapter(channel, simulation=False)
        else:
            return {
                "code": "CHANNEL_NOT_ENABLED",
                "message": exc.message,
                "status": IntentStatus.FAILED,
            }

    payload = _intent_payload(intent, consent, channel, scenario=test_scenario)
    eligibility = adapter.validate(payload)
    if not eligibility.eligible:
        intent.status = IntentStatus.FAILED
        db.commit()
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=eligibility.reason or "Not eligible",
        )

    adapter.prepare(payload)
    intent.status = IntentStatus.ATTEMPTING
    attempt = SubmissionAttempt(
        intent_id=intent.id,
        attempt_no=1,
        transport_state=IntentStatus.ATTEMPTING,
    )
    db.add(attempt)
    db.flush()

    outcome = adapter.submit(payload, idempotency_key=idempotency_key)
    attempt.transport_state = outcome.state.value
    attempt.sent_at = datetime.now(UTC) if outcome.state != OutcomeState.NOT_SENT else None
    attempt.external_message_id = outcome.provider_message_id
    attempt.unknown_outcome = outcome.state == OutcomeState.UNKNOWN_OUTCOME
    attempt.response_metadata_redacted = json.dumps(
        {**outcome.metadata, "message": outcome.message, "state": outcome.state.value}
    )

    intent.status = _outcome_to_intent_status(outcome.state)

    _append_timeline(
        db,
        complaint_id=complaint_id,
        actor_id=user_id,
        actor_kind=TimelineActorKind.SYSTEM,
        event_type="submission_attempt",
        public_payload={
            "outcome": outcome.state.value,
            "provider_message_id": outcome.provider_message_id,
        },
        idempotency_key=idempotency_key,
    )

    if outcome.official_reference:
        db.add(
            ExternalReference(
                complaint_id=complaint_id,
                intent_id=intent.id,
                reference_value=outcome.official_reference,
                tracking_url=outcome.tracking_url,
            )
        )

    db.commit()
    db.refresh(intent)

    return {
        "intent_id": intent.id,
        "status": intent.status,
        "outcome_state": outcome.state.value,
        "message": outcome.message,
        "provider_message_id": outcome.provider_message_id,
        "official_reference": outcome.official_reference,
        "metadata": outcome.metadata,
        "unknown_outcome": attempt.unknown_outcome,
        "attempt_no": attempt.attempt_no,
    }


def attest_sent(
    db: Session,
    *,
    user_id: str,
    intent_id: uuid.UUID,
    attestation_note: str | None = None,
) -> SubmissionIntent:
    intent = db.get(SubmissionIntent, intent_id)
    if intent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Intent not found")

    complaint = db.get(Complaint, intent.complaint_id)
    if complaint is None or complaint.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    if intent.status != IntentStatus.USER_ACTION_REQUIRED:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Attestation only allowed for guided handoffs",
        )

    intent.status = IntentStatus.ACK_PENDING
    _append_timeline(
        db,
        complaint_id=intent.complaint_id,
        actor_id=user_id,
        actor_kind=TimelineActorKind.CITIZEN,
        event_type="user_reported_sent",
        public_payload={"note": attestation_note} if attestation_note else None,
    )
    db.commit()
    db.refresh(intent)
    return intent


def attach_reference(
    db: Session,
    *,
    user_id: str,
    intent_id: uuid.UUID,
    reference_value: str,
    reference_type: str = "official_token",
    tracking_url: str | None = None,
) -> ExternalReference:
    intent = db.get(SubmissionIntent, intent_id)
    if intent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Intent not found")

    complaint = db.get(Complaint, intent.complaint_id)
    if complaint is None or complaint.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")

    ref = ExternalReference(
        complaint_id=intent.complaint_id,
        intent_id=intent.id,
        reference_value=reference_value.strip(),
        reference_type=reference_type,
        tracking_url=tracking_url,
    )
    db.add(ref)
    _append_timeline(
        db,
        complaint_id=intent.complaint_id,
        actor_id=user_id,
        actor_kind=TimelineActorKind.CITIZEN,
        event_type="user_provided_reference",
        public_payload={"reference_type": reference_type},
    )
    db.commit()
    db.refresh(ref)
    return ref


def reconcile_unknown(
    db: Session,
    *,
    admin_user_id: str,
    intent_id: uuid.UUID,
    determination: str,
) -> SubmissionIntent:
    intent = db.get(SubmissionIntent, intent_id)
    if intent is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Intent not found")

    if intent.status != IntentStatus.UNKNOWN_OUTCOME:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Reconciliation only for unknown outcomes",
        )

    latest = max(intent.attempts, key=lambda a: a.attempt_no, default=None)
    if latest is None or not latest.unknown_outcome:
        raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="No unknown attempt")

    if determination == "sent":
        intent.status = IntentStatus.ACK_PENDING
        latest.transport_state = OutcomeState.ACKNOWLEDGED.value
        latest.unknown_outcome = False
    elif determination == "not_sent":
        intent.status = IntentStatus.FAILED
        latest.transport_state = OutcomeState.NOT_SENT.value
        latest.unknown_outcome = False
    else:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid determination")

    _append_timeline(
        db,
        complaint_id=intent.complaint_id,
        actor_id=admin_user_id,
        actor_kind=TimelineActorKind.OFFICER,
        event_type="unknown_outcome_reconciled",
        public_payload={"determination": determination},
    )
    db.commit()
    db.refresh(intent)
    return intent
