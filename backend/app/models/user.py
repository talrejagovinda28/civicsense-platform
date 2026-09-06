from sqlalchemy import String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base
from app.models.base import TimestampMixin, UUIDPrimaryKeyMixin


class UserProfile(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Optional local profile linked to Clerk. Auth lives in Clerk."""

    __tablename__ = "user_profiles"

    clerk_user_id: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )
    display_name: Mapped[str | None] = mapped_column(String(200), nullable=True)
