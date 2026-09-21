import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.core.security import ClerkUser
from app.schemas.social import (
    AffectedResponse,
    BlockResponse,
    CommentCreateRequest,
    CommentResponse,
    FollowDecideRequest,
    FollowResponse,
    LikeResponse,
)
from app.services import social as social_service

router = APIRouter(tags=["social"])


@router.put("/complaints/{complaint_id}/like", response_model=LikeResponse)
def like_complaint(
    complaint_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: ClerkUser = Depends(get_current_user),
) -> LikeResponse:
    return LikeResponse.model_validate(
        social_service.like_complaint(db, user_id=current_user.user_id, complaint_id=complaint_id)
    )


@router.delete("/complaints/{complaint_id}/like", status_code=status.HTTP_204_NO_CONTENT)
def unlike_complaint(
    complaint_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: ClerkUser = Depends(get_current_user),
) -> None:
    social_service.unlike_complaint(db, user_id=current_user.user_id, complaint_id=complaint_id)


@router.put("/complaints/{complaint_id}/affected", response_model=AffectedResponse)
def mark_affected(
    complaint_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: ClerkUser = Depends(get_current_user),
) -> AffectedResponse:
    return AffectedResponse.model_validate(
        social_service.mark_affected(db, user_id=current_user.user_id, complaint_id=complaint_id)
    )


@router.delete("/complaints/{complaint_id}/affected", status_code=status.HTTP_204_NO_CONTENT)
def unmark_affected(
    complaint_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: ClerkUser = Depends(get_current_user),
) -> None:
    social_service.unmark_affected(db, user_id=current_user.user_id, complaint_id=complaint_id)


@router.get("/complaints/{complaint_id}/comments", response_model=list[CommentResponse])
def list_comments(
    complaint_id: uuid.UUID,
    db: Session = Depends(get_db),
) -> list[CommentResponse]:
    comments = social_service.list_comments(db, complaint_id=complaint_id)
    return [CommentResponse.model_validate(c) for c in comments]


@router.post("/complaints/{complaint_id}/comments", response_model=CommentResponse)
def create_comment(
    complaint_id: uuid.UUID,
    payload: CommentCreateRequest,
    db: Session = Depends(get_db),
    current_user: ClerkUser = Depends(get_current_user),
) -> CommentResponse:
    return CommentResponse.model_validate(
        social_service.create_comment(
            db,
            user_id=current_user.user_id,
            complaint_id=complaint_id,
            body=payload.body,
        )
    )


@router.delete("/comments/{comment_id}", response_model=CommentResponse)
def delete_comment(
    comment_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: ClerkUser = Depends(get_current_user),
) -> CommentResponse:
    return CommentResponse.model_validate(
        social_service.soft_delete_comment(
            db, user_id=current_user.user_id, comment_id=comment_id
        )
    )


@router.post("/profiles/{target_id}/follow", response_model=FollowResponse)
def follow_profile(
    target_id: str,
    db: Session = Depends(get_db),
    current_user: ClerkUser = Depends(get_current_user),
) -> FollowResponse:
    return FollowResponse.model_validate(
        social_service.follow_user(
            db, follower_id=current_user.user_id, target_id=target_id
        )
    )


@router.delete("/profiles/{target_id}/follow", status_code=status.HTTP_204_NO_CONTENT)
def unfollow_profile(
    target_id: str,
    db: Session = Depends(get_db),
    current_user: ClerkUser = Depends(get_current_user),
) -> None:
    social_service.unfollow_user(db, follower_id=current_user.user_id, target_id=target_id)


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
    return BlockResponse.model_validate(
        social_service.block_user(
            db, blocker_id=current_user.user_id, blocked_id=target_id
        )
    )


@router.delete("/profiles/{target_id}/block", status_code=status.HTTP_204_NO_CONTENT)
def unblock_profile(
    target_id: str,
    db: Session = Depends(get_db),
    current_user: ClerkUser = Depends(get_current_user),
) -> None:
    social_service.unblock_user(db, blocker_id=current_user.user_id, blocked_id=target_id)
