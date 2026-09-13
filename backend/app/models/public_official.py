from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class PublicOfficial(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "public_officials"

    city_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cities.id"),
        nullable=False,
        index=True,
    )
    full_name: Mapped[str] = mapped_column(String(200), nullable=False)
    party: Mapped[str | None] = mapped_column(String(100), nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source_license: Mapped[str | None] = mapped_column(String(100), nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    jurisdictions = relationship(
        "OfficialJurisdiction",
        back_populates="official",
        cascade="all, delete-orphan",
    )


class OfficialJurisdiction(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "official_jurisdictions"
    __table_args__ = (
        UniqueConstraint(
            "electoral_ward_id",
            "seat_label",
            name="uq_official_jurisdictions_ward_seat",
        ),
    )

    public_official_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("public_officials.id"),
        nullable=False,
    )
    electoral_ward_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("electoral_wards.id"),
        nullable=False,
        index=True,
    )
    seat_label: Mapped[str] = mapped_column(String(20), nullable=False)
    reservation: Mapped[str | None] = mapped_column(String(100), nullable=True)
    term_label: Mapped[str] = mapped_column(String(50), default="2026-2031", nullable=False)

    official = relationship("PublicOfficial", back_populates="jurisdictions")
    electoral_ward = relationship("ElectoralWard", backref="official_jurisdictions")
