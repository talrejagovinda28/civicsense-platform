from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from enum import StrEnum

from sqlalchemy import Float, ForeignKey, Integer, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.models.complaint import Complaint


class MediaResourceType(StrEnum):
    IMAGE = "image"
    VIDEO = "video"
    AUDIO = "audio"


class EvidenceKind(StrEnum):
    REPORT = "report"
    UPDATE = "update"
    RESOLUTION = "resolution"


class MediaVisibility(StrEnum):
    PUBLIC = "public"
    PRIVATE = "private"
    OWNER = "owner"
    INTERNAL = "internal"


class ComplaintImage(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "complaint_images"

    complaint_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("complaints.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    cloudinary_url: Mapped[str] = mapped_column(String(500), nullable=False)
    cloudinary_public_id: Mapped[str] = mapped_column(String(255), nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    resource_type: Mapped[str] = mapped_column(
        String(20),
        default=MediaResourceType.IMAGE,
        nullable=False,
    )
    duration_seconds: Mapped[float | None] = mapped_column(Float, nullable=True)
    evidence_kind: Mapped[str] = mapped_column(
        String(20),
        default=EvidenceKind.REPORT,
        nullable=False,
    )
    visibility: Mapped[str] = mapped_column(
        String(20),
        default=MediaVisibility.PUBLIC,
        nullable=False,
    )

    complaint: Mapped[Complaint] = relationship(back_populates="images")
