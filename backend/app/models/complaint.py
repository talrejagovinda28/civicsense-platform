from __future__ import annotations

import uuid
from enum import StrEnum
from typing import TYPE_CHECKING

from sqlalchemy import Boolean, Enum, Float, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.category import Category
    from app.models.city import City
    from app.models.complaint_image import ComplaintImage
    from app.models.complaint_status_history import ComplaintStatusHistory
    from app.models.electoral_ward import ElectoralWard
    from app.models.external_submission import ExternalSubmission
    from app.models.routing import Department
    from app.models.ward_office import WardOffice


class ComplaintStatus(StrEnum):
    SUBMITTED = "submitted"
    IN_PROGRESS = "in_progress"
    RESOLVED = "resolved"
    CLOSED = "closed"


class VerificationState(StrEnum):
    NONE = "none"
    PENDING = "pending"
    VERIFIED = "verified"
    DISPUTED = "disputed"


class SubmissionState(StrEnum):
    INTERNAL_CREATED = "internal_created"
    CONSENTED = "consented"
    DISPATCHED = "dispatched"
    RECEIPT_RECORDED = "receipt_recorded"


class RouteConfidence(StrEnum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    UNKNOWN = "unknown"


class Complaint(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "complaints"

    user_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[ComplaintStatus] = mapped_column(
        Enum(ComplaintStatus, name="complaint_status"),
        default=ComplaintStatus.SUBMITTED,
        nullable=False,
    )

    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("categories.id"),
        nullable=False,
    )
    ai_suggested_category_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("categories.id"),
        nullable=True,
    )
    ai_confidence: Mapped[float | None] = mapped_column(Float, nullable=True)

    latitude: Mapped[float | None] = mapped_column(nullable=True)
    longitude: Mapped[float | None] = mapped_column(nullable=True)
    google_place_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    address: Mapped[str] = mapped_column(String(500), nullable=False)
    ward: Mapped[str | None] = mapped_column(String(100), nullable=True)
    city: Mapped[str] = mapped_column(String(100), default="Pune", nullable=False)

    city_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cities.id"),
        nullable=True,
        index=True,
    )
    electoral_ward_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("electoral_wards.id"),
        nullable=True,
        index=True,
    )
    ward_office_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ward_offices.id"),
        nullable=True,
    )
    department_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("departments.id"),
        nullable=True,
    )
    public_latitude: Mapped[float | None] = mapped_column(nullable=True)
    public_longitude: Mapped[float | None] = mapped_column(nullable=True)
    anonymous_to_public: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    is_sensitive: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    public_caption: Mapped[str | None] = mapped_column(Text, nullable=True)
    verification_state: Mapped[str] = mapped_column(
        String(30),
        default=VerificationState.NONE,
        nullable=False,
    )
    submission_state: Mapped[str] = mapped_column(
        String(30),
        default=SubmissionState.INTERNAL_CREATED,
        nullable=False,
    )
    route_confidence: Mapped[str | None] = mapped_column(String(20), nullable=True)

    city_ref = relationship("City", foreign_keys=[city_id])
    electoral_ward = relationship("ElectoralWard", foreign_keys=[electoral_ward_id])
    ward_office = relationship("WardOffice", foreign_keys=[ward_office_id])
    department = relationship("Department", foreign_keys=[department_id])

    category: Mapped[Category] = relationship(
        foreign_keys=[category_id],
        back_populates="complaints",
    )
    images: Mapped[list[ComplaintImage]] = relationship(
        back_populates="complaint",
        cascade="all, delete-orphan",
    )
    status_history: Mapped[list[ComplaintStatusHistory]] = relationship(
        back_populates="complaint",
        cascade="all, delete-orphan",
        order_by="ComplaintStatusHistory.created_at",
    )
