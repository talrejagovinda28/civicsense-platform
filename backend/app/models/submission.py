from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class TimelineActorKind(StrEnum):
    CITIZEN = "citizen"
    SYSTEM = "system"
    OFFICER = "officer"
    PROVIDER = "provider"


class TimelineAuthenticityLevel(StrEnum):
    USER_ASSERTED = "user_asserted"
    SYSTEM_DERIVED = "system_derived"
    OFFICIAL_RECEIPT = "official_receipt"
    VERIFIED = "verified"


class TimelineVisibility(StrEnum):
    PUBLIC = "public"
    OWNER = "owner"
    INTERNAL = "internal"


class ExternalReferenceVisibility(StrEnum):
    OWNER = "owner"
    PUBLIC = "public"
    INTERNAL = "internal"


class SubmissionConsent(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "submission_consents"

    complaint_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("complaints.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    channel_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("external_channels.id"),
        nullable=True,
    )
    payload_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    disclosure_json: Mapped[str] = mapped_column(Text, nullable=False)
    version: Mapped[str] = mapped_column(String(20), nullable=False)
    authorized_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    revoked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    scope: Mapped[str] = mapped_column(String(50), nullable=False)

    complaint = relationship("Complaint", backref="submission_consents")
    channel = relationship("ExternalChannel")


class SubmissionIntent(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "submission_intents"

    complaint_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("complaints.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    consent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("submission_consents.id"),
        nullable=False,
    )
    channel_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("external_channels.id"),
        nullable=True,
    )
    destination_snapshot: Mapped[str] = mapped_column(Text, nullable=False)
    payload_hash: Mapped[str] = mapped_column(String(128), nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    status: Mapped[str] = mapped_column(String(30), nullable=False)
    test_scenario: Mapped[str | None] = mapped_column(String(50), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    complaint = relationship("Complaint", backref="submission_intents")
    consent = relationship("SubmissionConsent")
    channel = relationship("ExternalChannel")
    attempts = relationship("SubmissionAttempt", back_populates="intent")


class SubmissionAttempt(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "submission_attempts"
    __table_args__ = (
        UniqueConstraint("intent_id", "attempt_no", name="uq_submission_attempts_intent_no"),
    )

    intent_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("submission_intents.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    attempt_no: Mapped[int] = mapped_column(Integer, nullable=False)
    transport_state: Mapped[str] = mapped_column(String(30), nullable=False)
    external_message_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    error_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    unknown_outcome: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    response_metadata_redacted: Mapped[str | None] = mapped_column(Text, nullable=True)

    intent = relationship("SubmissionIntent", back_populates="attempts")


class ExternalReference(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "external_references"

    complaint_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("complaints.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    intent_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("submission_intents.id"),
        nullable=True,
    )
    reference_value: Mapped[str] = mapped_column(String(255), nullable=False)
    reference_type: Mapped[str] = mapped_column(String(50), nullable=False)
    evidence_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    tracking_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    visibility: Mapped[str] = mapped_column(
        String(20),
        default=ExternalReferenceVisibility.OWNER,
        nullable=False,
    )

    complaint = relationship("Complaint", backref="external_references")
    intent = relationship("SubmissionIntent")


class ComplaintTimelineEvent(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "complaint_timeline_events"

    complaint_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("complaints.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    actor_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    actor_kind: Mapped[str] = mapped_column(String(30), nullable=False)
    event_type: Mapped[str] = mapped_column(String(50), nullable=False)
    authenticity_level: Mapped[str] = mapped_column(String(30), nullable=False)
    public_payload_redacted: Mapped[str | None] = mapped_column(Text, nullable=True)
    visibility: Mapped[str] = mapped_column(String(20), nullable=False)
    idempotency_key: Mapped[str | None] = mapped_column(String(128), unique=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    complaint = relationship("Complaint", backref="timeline_events")
