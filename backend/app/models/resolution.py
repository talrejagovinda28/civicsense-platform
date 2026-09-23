from __future__ import annotations

import uuid
from enum import StrEnum

from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class ResolutionEvidenceStatus(StrEnum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class ResolutionEvidence(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "resolution_evidence"

    complaint_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("complaints.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    submitter_id: Mapped[str] = mapped_column(String(255), nullable=False)
    submitter_role: Mapped[str] = mapped_column(String(30), nullable=False)
    media_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    assertion: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[str] = mapped_column(
        String(30),
        default=ResolutionEvidenceStatus.PENDING,
        nullable=False,
    )

    complaint = relationship("Complaint", backref="resolution_evidence")
    reviews = relationship("ResolutionReview", back_populates="evidence")


class ResolutionReview(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "resolution_reviews"

    complaint_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("complaints.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    evidence_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("resolution_evidence.id"),
        nullable=True,
    )
    decision: Mapped[str] = mapped_column(String(30), nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)
    reviewer_id: Mapped[str] = mapped_column(String(255), nullable=False)

    complaint = relationship("Complaint", backref="resolution_reviews")
    evidence = relationship("ResolutionEvidence", back_populates="reviews")
