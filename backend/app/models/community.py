from __future__ import annotations

import uuid
from datetime import datetime
from enum import StrEnum

from sqlalchemy import DateTime, ForeignKey, String, Text, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class FeedEventKind(StrEnum):
    ORIGINAL = "original"
    MILESTONE = "milestone"


class FeedVisibility(StrEnum):
    PUBLIC = "public"
    OWNER = "owner"
    FOLLOWERS = "followers"


class FollowStatus(StrEnum):
    REQUESTED = "requested"
    ACCEPTED = "accepted"
    DECLINED = "declined"


class ModerationStatus(StrEnum):
    VISIBLE = "visible"
    HIDDEN = "hidden"
    REMOVED = "removed"


class FeedEvent(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "feed_events"

    complaint_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("complaints.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    kind: Mapped[str] = mapped_column(String(30), nullable=False)
    timeline_event_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("complaint_timeline_events.id"),
        nullable=True,
    )
    published_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    visibility: Mapped[str] = mapped_column(
        String(20),
        default=FeedVisibility.PUBLIC,
        nullable=False,
    )

    complaint = relationship("Complaint", backref="feed_events")
    timeline_event = relationship("ComplaintTimelineEvent")


class Like(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "likes"
    __table_args__ = (UniqueConstraint("user_id", "complaint_id", name="uq_likes_user_complaint"),)

    user_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    complaint_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("complaints.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    complaint = relationship("Complaint", backref="likes")


class Affected(Base, UUIDPrimaryKeyMixin):
    __tablename__ = "affected"
    __table_args__ = (
        UniqueConstraint("user_id", "complaint_id", name="uq_affected_user_complaint"),
    )

    user_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    complaint_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("complaints.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    complaint = relationship("Complaint", backref="affected_confirmations")


class Comment(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "comments"

    complaint_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("complaints.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    author_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    body: Mapped[str] = mapped_column(Text, nullable=False)
    deleted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    moderation_status: Mapped[str] = mapped_column(
        String(20),
        default=ModerationStatus.VISIBLE,
        nullable=False,
    )

    complaint = relationship("Complaint", backref="comments")


class Follow(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "follows"
    __table_args__ = (
        UniqueConstraint("follower_id", "target_id", name="uq_follows_follower_target"),
    )

    follower_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    target_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    accepted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)


class UserBlock(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "user_blocks"
    __table_args__ = (
        UniqueConstraint("blocker_id", "blocked_id", name="uq_user_blocks_blocker_blocked"),
    )

    blocker_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)
    blocked_id: Mapped[str] = mapped_column(String(255), nullable=False, index=True)


class ComplaintRelated(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    __tablename__ = "complaint_related"
    __table_args__ = (
        UniqueConstraint(
            "complaint_id_a",
            "complaint_id_b",
            name="uq_complaint_related_pair",
        ),
    )

    complaint_id_a: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("complaints.id", ondelete="CASCADE"),
        nullable=False,
    )
    complaint_id_b: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("complaints.id", ondelete="CASCADE"),
        nullable=False,
    )
    reason: Mapped[str] = mapped_column(String(100), nullable=False)
