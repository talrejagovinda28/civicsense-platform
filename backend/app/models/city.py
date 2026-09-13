from __future__ import annotations

from enum import StrEnum

from sqlalchemy import Boolean, Float, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class CityStatus(StrEnum):
    ACTIVE = "active"
    PREVIEW = "preview"
    DISABLED = "disabled"


class City(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "cities"

    slug: Mapped[str] = mapped_column(String(100), unique=True, nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    state_name: Mapped[str] = mapped_column(String(100), nullable=False)
    state_code: Mapped[str | None] = mapped_column(String(10), nullable=True)
    country_code: Mapped[str] = mapped_column(String(2), default="IN", nullable=False)
    status: Mapped[CityStatus] = mapped_column(
        String(20),
        default=CityStatus.PREVIEW,
        nullable=False,
    )
    municipality_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    center_lat: Mapped[float] = mapped_column(Float, nullable=False)
    center_lng: Mapped[float] = mapped_column(Float, nullable=False)
    default_zoom: Mapped[int] = mapped_column(Integer, default=12, nullable=False)
    supports_reporting: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    supports_ward_map: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    supports_accountability: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    map_data_version: Mapped[str | None] = mapped_column(String(50), nullable=True)
