from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class ElectoralWard(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "electoral_wards"
    __table_args__ = (UniqueConstraint("city_id", "ward_no", name="uq_electoral_wards_city_ward_no"),)

    city_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cities.id"),
        nullable=False,
        index=True,
    )
    external_code: Mapped[str | None] = mapped_column(String(50), nullable=True)
    ward_no: Mapped[int] = mapped_column(Integer, nullable=False)
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    geometry_feature_id: Mapped[str] = mapped_column(String(100), nullable=False)
    valid_from: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    valid_to: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    source_license: Mapped[str | None] = mapped_column(String(100), nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    city = relationship("City", backref="electoral_wards")
