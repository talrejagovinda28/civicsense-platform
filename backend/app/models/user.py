from enum import StrEnum

from sqlalchemy import Boolean, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class DmPolicy(StrEnum):
    MUTUAL_OR_REQUEST = "mutual_or_request"
    FOLLOWERS = "followers"
    NONE = "none"


class UserProfile(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Optional local profile linked to Clerk. Auth lives in Clerk."""

    __tablename__ = "user_profiles"

    clerk_user_id: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    handle: Mapped[str | None] = mapped_column(String(50), unique=True, nullable=True)
    display_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
    bio: Mapped[str | None] = mapped_column(Text, nullable=True)
    is_private: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    dm_policy: Mapped[str] = mapped_column(
        String(30),
        default=DmPolicy.MUTUAL_OR_REQUEST,
        nullable=False,
    )
    official_dm_opt_in: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    home_locality_label: Mapped[str | None] = mapped_column(String(200), nullable=True)
