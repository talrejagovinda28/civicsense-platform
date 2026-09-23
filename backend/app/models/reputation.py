from __future__ import annotations

from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, Integer, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.base import UUIDPrimaryKeyMixin


class ReputationStatus(StrEnum):
    GRANTED = "granted"
    REVERSED = "reversed"
    PENDING = "pending"


class ReputationLedger(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "reputation_ledger"

    user_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    event_key: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    source_entity_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    kind: Mapped[str] = mapped_column(String(50), nullable=False)
    delta: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(
        String(20),
        default=ReputationStatus.GRANTED,
        nullable=False,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )


class BadgeAward(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "badge_awards"

    user_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    badge_code: Mapped[str] = mapped_column(String(50), nullable=False)
    source_event_key: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    granted_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
