import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db, get_optional_user
from app.core.security import ClerkUser
from app.schemas.social import (
    BlockResponse,
    CommentCreateRequest,
    CommentItem,
    EngagementCounts,
    FollowDecideRequest,
    FollowResponse,
    PaginatedComments,
)
from app.services import social as social_service
from app.services.access import assert_complaint_socially_visible
from app.services.profiles import resolve_follow_target_id

router = APIRouter(tags=["social"])


def _viewer_context(user: ClerkUser | None) -> tuple[str | None, str | None]:
    if user is None:
        return None, None
    return user.user_id, user.role


@router.get("/complaints/{complaint_id}/engagement", response_model=EngagementCounts)
def get_complaint_engagement(
    complaint_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: ClerkUser | None = Depends(get_optional_user),
) -> EngagementCounts:
    viewer_id, role = _viewer_context(current_user)
    assert_complaint_socially_visible(db, complaint_id, viewer_id, role)
    return social_service.get_engagement_counts(
        db,
        complaint_id=complaint_id,
        viewer_id=viewer_id,
    )


@router.put("/complaints/{complaint_id}/like", response_model=EngagementCounts)
def like_complaint(
    complaint_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: ClerkUser = Depends(get_current_user),
) -> EngagementCounts:
    assert_complaint_socially_visible(
        db, complaint_id, current_user.user_id, current_user.role
    )
    social_service.like_complaint(
        db, user_id=current_user.user_id, complaint_id=complaint_id
    )
    return social_service.get_engagement_counts(
        db,
        complaint_id=complaint_id,
        viewer_id=current_user.user_id,
    )


@router.delete("/complaints/{complaint_id}/like", response_model=EngagementCounts)
def unlike_complaint(
    complaint_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: ClerkUser = Depends(get_current_user),
) -> EngagementCounts:
    assert_complaint_socially_visible(
        db, complaint_id, current_user.user_id, current_user.role
    )
    social_service.unlike_complaint(
        db, user_id=current_user.user_id, complaint_id=complaint_id
    )
    return social_service.get_engagement_counts(
        db,
        complaint_id=complaint_id,
        viewer_id=current_user.user_id,
    )


@router.put("/complaints/{complaint_id}/affected", response_model=EngagementCounts)
def mark_affected(
    complaint_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: ClerkUser = Depends(get_current_user),
) -> EngagementCounts:
    assert_complaint_socially_visible(
        db, complaint_id, current_user.user_id, current_user.role
    )
    social_service.mark_affected(
        db, user_id=current_user.user_id, complaint_id=complaint_id
    )
    return social_service.get_engagement_counts(
        db,
        complaint_id=complaint_id,
        viewer_id=current_user.user_id,
    )


@router.delete("/complaints/{complaint_id}/affected", response_model=EngagementCounts)
def unmark_affected(
    complaint_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: ClerkUser = Depends(get_current_user),
) -> EngagementCounts:
    assert_complaint_socially_visible(
        db, complaint_id, current_user.user_id, current_user.role
    )
    social_service.unmark_affected(
        db, user_id=current_user.user_id, complaint_id=complaint_id
    )
    return social_service.get_engagement_counts(
        db,
        complaint_id=complaint_id,
        viewer_id=current_user.user_id,
    )


@router.get("/complaints/{complaint_id}/comments", response_model=PaginatedComments)
def list_comments(
    complaint_id: uuid.UUID,
    skip: int = Query(default=0, ge=0),
    limit: int = Query(default=30, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: ClerkUser | None = Depends(get_optional_user),
) -> PaginatedComments:
    viewer_id, role = _viewer_context(current_user)
    complaint = assert_complaint_socially_visible(db, complaint_id, viewer_id, role)
    comments = social_service.list_comments(
        db, complaint_id=complaint_id, skip=skip, limit=limit
    )
    total = social_service.count_comments(db, complaint_id=complaint_id)
    return PaginatedComments(
        items=[
            social_service.comment_to_item(db, comment, complaint) for comment in comments
        ],
        total=total,
        skip=skip,
        limit=limit,
    )


@router.post("/complaints/{complaint_id}/comments", response_model=CommentItem)
def create_comment(
    complaint_id: uuid.UUID,
    payload: CommentCreateRequest,
    db: Session = Depends(get_db),
    current_user: ClerkUser = Depends(get_current_user),
) -> CommentItem:
    complaint = assert_complaint_socially_visible(
        db, complaint_id, current_user.user_id, current_user.role
    )
    comment = social_service.create_comment(
        db,
        user_id=current_user.user_id,
        complaint_id=complaint_id,
        body=payload.body,
    )
    return social_service.comment_to_item(db, comment, complaint)


@router.delete("/comments/{comment_id}", response_model=CommentItem)
def delete_comment(
    comment_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: ClerkUser = Depends(get_current_user),
) -> CommentItem:
    comment = social_service.soft_delete_comment(
        db, user_id=current_user.user_id, comment_id=comment_id
    )
    complaint = assert_complaint_socially_visible(
        db, comment.complaint_id, current_user.user_id, current_user.role
    )
    return social_service.comment_to_item(db, comment, complaint)


@router.post("/profiles/{target_id}/follow", response_model=FollowResponse)
def follow_profile(
    target_id: str,
    db: Session = Depends(get_db),
    current_user: ClerkUser = Depends(get_current_user),
) -> FollowResponse:
    clerk_target_id = resolve_follow_target_id(db, target_id)
    return FollowResponse.model_validate(
        social_service.follow_user(
            db, follower_id=current_user.user_id, target_id=clerk_target_id
        )
    )


@router.delete("/profiles/{target_id}/follow", status_code=204)
def unfollow_profile(
    target_id: str,
    db: Session = Depends(get_db),
    current_user: ClerkUser = Depends(get_current_user),
) -> None:
    clerk_target_id = resolve_follow_target_id(db, target_id)
    social_service.unfollow_user(
        db, follower_id=current_user.user_id, target_id=clerk_target_id
    )


@router.post("/follow-requests/{follow_id}/decide", response_model=FollowResponse)
def decide_follow(
    follow_id: uuid.UUID,
    payload: FollowDecideRequest,
    db: Session = Depends(get_db),
    current_user: ClerkUser = Depends(get_current_user),
) -> FollowResponse:
    return FollowResponse.model_validate(
        social_service.decide_follow_request(
            db,
            target_id=current_user.user_id,
            follow_id=follow_id,
            accept=payload.accept,
        )
    )


@router.post("/profiles/{target_id}/block", response_model=BlockResponse)
def block_profile(
    target_id: str,
    db: Session = Depends(get_db),
    current_user: ClerkUser = Depends(get_current_user),
) -> BlockResponse:
    clerk_target_id = resolve_follow_target_id(db, target_id)
    return BlockResponse.model_validate(
        social_service.block_user(
            db, blocker_id=current_user.user_id, blocked_id=clerk_target_id
        )
    )


@router.delete("/profiles/{target_id}/block", status_code=204)
def unblock_profile(
    target_id: str,
    db: Session = Depends(get_db),
    current_user: ClerkUser = Depends(get_current_user),
) -> None:
    clerk_target_id = resolve_follow_target_id(db, target_id)
    social_service.unblock_user(
        db, blocker_id=current_user.user_id, blocked_id=clerk_target_id
    )
