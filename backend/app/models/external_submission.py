from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, ForeignKey, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class ExternalSubmissionStatus(StrEnum):
    NOT_STARTED = "not_started"
    HANDOFF_STARTED = "handoff_started"
    TOKEN_RECEIVED = "token_received"


class ExternalSubmission(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "external_submissions"

    complaint_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("complaints.id"),
        nullable=False,
        unique=True,
    )
    routing_channel_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("routing_channels.id"),
        nullable=True,
    )
    provider: Mapped[str] = mapped_column(String(50), default="pmc_care", nullable=False)
    status: Mapped[ExternalSubmissionStatus] = mapped_column(
        String(30),
        default=ExternalSubmissionStatus.NOT_STARTED,
        nullable=False,
    )
    external_token: Mapped[str | None] = mapped_column(String(120), nullable=True)
    status_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    forwarded_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    token_received_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    complaint = relationship("Complaint", backref="external_submission", uselist=False)
    routing_channel = relationship("RoutingChannel")
