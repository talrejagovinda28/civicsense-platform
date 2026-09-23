from __future__ import annotations

import uuid
from datetime import date, datetime
from enum import StrEnum

from sqlalchemy import Boolean, Date, DateTime, ForeignKey, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class AuthoritySourceStatus(StrEnum):
    RESEARCH_ONLY = "research_only"
    VERIFIED = "verified"
    DEPRECATED = "deprecated"


class ChannelActivation(StrEnum):
    DISABLED = "DISABLED"
    TEST_ONLY = "TEST_ONLY"
    MANUAL = "MANUAL"
    AUTOMATED = "AUTOMATED"
    LIVE_APPROVED = "LIVE_APPROVED"


class ChannelMode(StrEnum):
    GUIDED_PORTAL = "GUIDED_PORTAL"
    GUIDED_WHATSAPP = "GUIDED_WHATSAPP"
    EMAIL = "EMAIL"
    API = "API"


class AuthoritySource(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "authority_sources"

    origin_url: Mapped[str] = mapped_column(String(500), nullable=False)
    title: Mapped[str] = mapped_column(String(300), nullable=False)
    publisher: Mapped[str] = mapped_column(String(200), nullable=False)
    publication_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    evidence_type: Mapped[str] = mapped_column(String(50), nullable=False)
    validation_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[AuthoritySourceStatus] = mapped_column(
        String(30),
        default=AuthoritySourceStatus.RESEARCH_ONLY,
        nullable=False,
    )


class ExternalChannel(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "external_channels"

    city_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("cities.id"),
        nullable=False,
        index=True,
    )
    routing_channel_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("routing_channels.id"),
        nullable=True,
    )
    channel_type: Mapped[str] = mapped_column(String(50), nullable=False)
    mode: Mapped[str] = mapped_column(String(50), nullable=False)
    activation: Mapped[str] = mapped_column(
        String(30),
        default=ChannelActivation.DISABLED,
        nullable=False,
    )
    destination: Mapped[str] = mapped_column(String(500), nullable=False)
    source_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("authority_sources.id"),
        nullable=True,
    )
    can_auto_submit: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    supports_tracking: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    on_behalf_policy: Mapped[str] = mapped_column(String(50), nullable=False)
    enabled: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    disable_reason: Mapped[str | None] = mapped_column(String(500), nullable=True)
    checked_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    city = relationship("City", backref="external_channels")
    routing_channel = relationship("RoutingChannel")
    source = relationship("AuthoritySource")
