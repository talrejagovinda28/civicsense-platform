from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class WardJurisdictionMapping(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "ward_jurisdiction_mappings"
    __table_args__ = (
        UniqueConstraint(
            "electoral_ward_id",
            name="uq_ward_jurisdiction_mappings_electoral_ward",
        ),
    )

    electoral_ward_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("electoral_wards.id"),
        nullable=False,
    )
    ward_office_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("ward_offices.id"),
        nullable=False,
    )
    confidence: Mapped[str] = mapped_column(String(20), default="verified", nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    electoral_ward = relationship("ElectoralWard", backref="ward_office_mappings")
    ward_office = relationship("WardOffice", backref="electoral_mappings")
