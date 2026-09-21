from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.core.security import ClerkUser
from app.models.reputation import BadgeAward
from app.models.user import UserProfile
from app.schemas.profile import ProfileResponse, ProfileUpdateRequest, ReputationResponse
from app.services.reputation import can_create_group, can_initiate_dm, get_lifetime_xp

router = APIRouter(prefix="/profiles", tags=["profiles"])


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


@router.get("/me", response_model=ProfileResponse)
def get_my_profile(
    db: Session = Depends(get_db),
    current_user: ClerkUser = Depends(get_current_user),
) -> ProfileResponse:
    profile = _ensure_profile(db, current_user.user_id)
    return ProfileResponse(
        id=profile.id,
        user_id=profile.clerk_user_id,
        handle=profile.handle or f"user_{profile.clerk_user_id[:8]}",
        display_name=profile.display_name,
        bio=profile.bio,
        is_private=profile.is_private,
        dm_policy=profile.dm_policy,
        created_at=profile.created_at,
    )


@router.patch("/me", response_model=ProfileResponse)
def update_my_profile(
    payload: ProfileUpdateRequest,
    db: Session = Depends(get_db),
    current_user: ClerkUser = Depends(get_current_user),
) -> ProfileResponse:
    profile = _ensure_profile(db, current_user.user_id)
    data = payload.model_dump(exclude_unset=True)
    for key, value in data.items():
        setattr(profile, key, value)
    db.commit()
    db.refresh(profile)
    return ProfileResponse(
        id=profile.id,
        user_id=profile.clerk_user_id,
        handle=profile.handle or f"user_{profile.clerk_user_id[:8]}",
        display_name=profile.display_name,
        bio=profile.bio,
        is_private=profile.is_private,
        dm_policy=profile.dm_policy,
        created_at=profile.created_at,
    )


@router.get("/me/reputation", response_model=ReputationResponse)
def get_my_reputation(
    db: Session = Depends(get_db),
    current_user: ClerkUser = Depends(get_current_user),
) -> ReputationResponse:
    user_id = current_user.user_id
    badges = list(
        db.scalars(select(BadgeAward.badge_code).where(BadgeAward.user_id == user_id))
    )
    return ReputationResponse(
        lifetime_xp=get_lifetime_xp(db, user_id),
        can_initiate_dm=can_initiate_dm(db, user_id),
        can_create_group=can_create_group(db, user_id),
        badges=badges,
    )


@router.get("/{handle}", response_model=ProfileResponse)
def get_public_profile(handle: str, db: Session = Depends(get_db)) -> ProfileResponse:
    profile = db.scalar(select(UserProfile).where(UserProfile.handle == handle))
    if profile is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Profile not found")
    if profile.is_private:
        return ProfileResponse(
            id=profile.id,
            user_id="",
            handle=profile.handle or handle,
            display_name=profile.display_name,
            is_private=True,
            dm_policy=profile.dm_policy,
            created_at=profile.created_at,
        )
    return ProfileResponse(
        id=profile.id,
        user_id="",
        handle=profile.handle or handle,
        display_name=profile.display_name,
        bio=profile.bio,
        is_private=profile.is_private,
        dm_policy=profile.dm_policy,
        created_at=profile.created_at,
    )
