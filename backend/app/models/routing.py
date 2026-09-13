from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class Department(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "departments"
    __table_args__ = (UniqueConstraint("city_id", "slug", name="uq_departments_city_slug"),)

    city_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cities.id"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(200), nullable=False)
    slug: Mapped[str] = mapped_column(String(120), nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    city = relationship("City", backref="departments")


class CategoryRoutingRule(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "category_routing_rules"
    __table_args__ = (
        UniqueConstraint("city_id", "category_id", name="uq_category_routing_city_category"),
    )

    city_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cities.id"),
        nullable=False,
    )
    category_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("categories.id"),
        nullable=False,
    )
    department_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("departments.id"),
        nullable=False,
    )
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)

    department = relationship("Department", backref="category_rules")
    category = relationship("Category", backref="routing_rules")


class RoutingChannel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "routing_channels"

    city_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cities.id"),
        nullable=False,
        index=True,
    )
    channel_type: Mapped[str] = mapped_column(String(50), nullable=False)
    label: Mapped[str] = mapped_column(String(200), nullable=False)
    value: Mapped[str] = mapped_column(String(500), nullable=False)
    url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    is_official: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)
    verified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    notes: Mapped[str | None] = mapped_column(String(500), nullable=True)

    city = relationship("City", backref="routing_channels")
