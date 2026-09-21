from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db, get_optional_user
from app.core.security import ClerkUser
from app.models.reputation import BadgeAward
from app.models.user import UserProfile
from app.schemas.profile import (
    BadgeItem,
    OwnProfileResponse,
    ProfileResponse,
    ProfileUpdateRequest,
    ReputationResponse,
    ReputationUnlocks,
)
from app.services.profiles import build_own_profile_response, build_profile_response
from app.services.reputation import can_create_group, can_initiate_dm, get_lifetime_xp

router = APIRouter(prefix="/profiles", tags=["profiles"])

_BADGE_LABELS: dict[str, str] = {
    "first_report": "First Report",
    "trusted_reporter": "Trusted Reporter",
    "resolution_helper": "Resolution Helper",
}


def _ensure_profile(db: Session, user_id: str) -> UserProfile:
    profile = db.scalar(select(UserProfile).where(UserProfile.clerk_user_id == user_id))
    if profile is not None:
        return profile
    handle = f"user_{user_id[:8]}"
    profile = UserProfile(clerk_user_id=user_id, handle=handle)
    db.add(profile)
    db.commit()
    db.refresh(profile)
    return profile


@router.get("/me", response_model=OwnProfileResponse)
def get_my_profile(
    db: Session = Depends(get_db),
    current_user: ClerkUser = Depends(get_current_user),
) -> OwnProfileResponse:
    profile = _ensure_profile(db, current_user.user_id)
    return build_own_profile_response(db, profile)


@router.patch("/me", response_model=OwnProfileResponse)
def update_my_profile(
    payload: ProfileUpdateRequest,
    db: Session = Depends(get_db),
    current_user: ClerkUser = Depends(get_current_user),
) -> OwnProfileResponse:
    profile = _ensure_profile(db, current_user.user_id)
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(profile, key, value)
    db.commit()
    db.refresh(profile)
    return build_own_profile_response(db, profile)


@router.get("/me/reputation", response_model=ReputationResponse)
def get_my_reputation(
    db: Session = Depends(get_db),
    current_user: ClerkUser = Depends(get_current_user),
) -> ReputationResponse:
    user_id = current_user.user_id
    badge_rows = list(
        db.scalars(select(BadgeAward).where(BadgeAward.user_id == user_id))
    )
    lifetime_xp = get_lifetime_xp(db, user_id)
    return ReputationResponse(
        lifetime_xp=lifetime_xp,
        eligible_xp=lifetime_xp,
        badges=[
            BadgeItem(
                code=row.badge_code,
                label=_BADGE_LABELS.get(row.badge_code, row.badge_code.replace("_", " ").title()),
                granted_at=row.granted_at,
            )
            for row in badge_rows
        ],
        unlocks=ReputationUnlocks(
            can_initiate_dm=can_initiate_dm(db, user_id),
            can_create_group=can_create_group(db, user_id),
        ),
    )


@router.get("/{handle}", response_model=ProfileResponse)
def get_public_profile(
    handle: str,
    db: Session = Depends(get_db),
    viewer: ClerkUser | None = Depends(get_optional_user),
) -> ProfileResponse:
    profile = db.scalar(select(UserProfile).where(UserProfile.handle == handle))
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")

    viewer_id = viewer.user_id if viewer else None
    if profile.is_private and viewer_id != profile.clerk_user_id:
        if viewer_id is None:
            return ProfileResponse(
                id=profile.id,
                handle=profile.handle or handle,
                display_name=profile.display_name,
                is_private=True,
            )
        response = build_profile_response(db, profile, viewer_id=viewer_id)
        if not response.viewer_is_following:
            return ProfileResponse(
                id=profile.id,
                handle=profile.handle or handle,
                display_name=profile.display_name,
                is_private=True,
                viewer_is_following=response.viewer_is_following,
                viewer_follow_pending=response.viewer_follow_pending,
            )

    return build_profile_response(db, profile, viewer_id=viewer_id)
