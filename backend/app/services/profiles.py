from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.community import Follow, FollowStatus
from app.models.user import UserProfile
from app.schemas.profile import OwnProfileResponse, ProfileResponse


def _follower_count(db: Session, clerk_user_id: str) -> int:
    return int(
        db.scalar(
            select(func.count())
            .select_from(Follow)
            .where(
                Follow.target_id == clerk_user_id,
                Follow.status == FollowStatus.ACCEPTED,
            )
        )
        or 0
    )


def _following_count(db: Session, clerk_user_id: str) -> int:
    return int(
        db.scalar(
            select(func.count())
            .select_from(Follow)
            .where(
                Follow.follower_id == clerk_user_id,
                Follow.status == FollowStatus.ACCEPTED,
            )
        )
        or 0
    )


def _viewer_follow_state(
    db: Session,
    *,
    viewer_id: str | None,
    target_id: str,
) -> tuple[bool, bool]:
    if viewer_id is None or viewer_id == target_id:
        return False, False

    follow = db.scalar(
        select(Follow).where(
            Follow.follower_id == viewer_id,
            Follow.target_id == target_id,
        )
    )
    if follow is None:
        return False, False
    if follow.status == FollowStatus.ACCEPTED:
        return True, False
    if follow.status == FollowStatus.REQUESTED:
        return False, True
    return False, False


def build_profile_response(
    db: Session,
    profile: UserProfile,
    *,
    viewer_id: str | None = None,
) -> ProfileResponse:
    viewer_is_following, viewer_follow_pending = _viewer_follow_state(
        db,
        viewer_id=viewer_id,
        target_id=profile.clerk_user_id,
    )
    return ProfileResponse(
        id=profile.id,
        handle=profile.handle or f"user_{profile.clerk_user_id[:8]}",
        display_name=profile.display_name,
        bio=profile.bio,
        is_private=profile.is_private,
        follower_count=_follower_count(db, profile.clerk_user_id),
        following_count=_following_count(db, profile.clerk_user_id),
        viewer_is_following=viewer_is_following,
        viewer_follow_pending=viewer_follow_pending,
        messaging_user_id=profile.clerk_user_id,
    )


def build_own_profile_response(db: Session, profile: UserProfile) -> OwnProfileResponse:
    base = build_profile_response(db, profile, viewer_id=profile.clerk_user_id)
    return OwnProfileResponse(
        **base.model_dump(),
        home_locality=profile.home_locality_label,
    )


def resolve_follow_target_id(db: Session, target_id: str) -> str:
    """Accept Clerk user id (preferred) or profile UUID."""
    try:
        profile_uuid = uuid.UUID(target_id)
    except ValueError:
        return target_id

    profile = db.get(UserProfile, profile_uuid)
    if profile is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Profile not found",
        )
    return profile.clerk_user_id
