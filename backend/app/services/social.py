from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.community import Affected, Comment, Follow, FollowStatus, Like, ModerationStatus, UserBlock
from app.models.user import DmPolicy, UserProfile


def _is_blocked(db: Session, user_a: str, user_b: str) -> bool:
    return (
        db.scalar(
            select(UserBlock).where(
                UserBlock.blocker_id == user_b,
                UserBlock.blocked_id == user_a,
            )
        )
        is not None
    )


def like_complaint(db: Session, *, user_id: str, complaint_id: uuid.UUID) -> Like:
    existing = db.scalar(
        select(Like).where(Like.user_id == user_id, Like.complaint_id == complaint_id)
    )
    if existing is not None:
        return existing
    like = Like(user_id=user_id, complaint_id=complaint_id, created_at=datetime.now(UTC))
    db.add(like)
    db.commit()
    db.refresh(like)
    return like


def unlike_complaint(db: Session, *, user_id: str, complaint_id: uuid.UUID) -> None:
    like = db.scalar(
        select(Like).where(Like.user_id == user_id, Like.complaint_id == complaint_id)
    )
    if like is None:
        return
    db.delete(like)
    db.commit()


def mark_affected(db: Session, *, user_id: str, complaint_id: uuid.UUID) -> Affected:
    row = Affected(user_id=user_id, complaint_id=complaint_id, created_at=datetime.now(UTC))
    db.add(row)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = db.scalar(
            select(Affected).where(
                Affected.user_id == user_id, Affected.complaint_id == complaint_id
            )
        )
        if existing is None:
            raise
        return existing
    db.refresh(row)
    return row


def unmark_affected(db: Session, *, user_id: str, complaint_id: uuid.UUID) -> None:
    row = db.scalar(
        select(Affected).where(
            Affected.user_id == user_id, Affected.complaint_id == complaint_id
        )
    )
    if row is None:
        return
    db.delete(row)
    db.commit()


def create_comment(
    db: Session,
    *,
    user_id: str,
    complaint_id: uuid.UUID,
    body: str,
) -> Comment:
    comment = Comment(
        complaint_id=complaint_id,
        author_id=user_id,
        body=body.strip(),
        moderation_status=ModerationStatus.VISIBLE,
    )
    db.add(comment)
    db.commit()
    db.refresh(comment)
    return comment


def list_comments(
    db: Session,
    *,
    complaint_id: uuid.UUID,
    limit: int = 50,
) -> list[Comment]:
    return list(
        db.scalars(
            select(Comment)
            .where(
                Comment.complaint_id == complaint_id,
                Comment.deleted_at.is_(None),
                Comment.moderation_status == ModerationStatus.VISIBLE,
            )
            .order_by(Comment.created_at.asc())
            .limit(limit)
        )
    )


def soft_delete_comment(db: Session, *, user_id: str, comment_id: uuid.UUID) -> Comment:
    comment = db.get(Comment, comment_id)
    if comment is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Comment not found")
    if comment.author_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not authorized")
    comment.deleted_at = datetime.now(UTC)
    db.commit()
    db.refresh(comment)
    return comment


def follow_user(db: Session, *, follower_id: str, target_id: str) -> Follow:
    if follower_id == target_id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Cannot self-follow")
    if _is_blocked(db, follower_id, target_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Blocked")

    target_profile = db.scalar(select(UserProfile).where(UserProfile.clerk_user_id == target_id))
    follow_status = (
        FollowStatus.REQUESTED
        if target_profile and target_profile.is_private
        else FollowStatus.ACCEPTED
    )
    follow = Follow(
        follower_id=follower_id,
        target_id=target_id,
        status=follow_status,
        accepted_at=datetime.now(UTC) if follow_status == FollowStatus.ACCEPTED else None,
    )
    db.add(follow)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = db.scalar(
            select(Follow).where(
                Follow.follower_id == follower_id, Follow.target_id == target_id
            )
        )
        if existing is None:
            raise
        return existing
    db.refresh(follow)
    return follow


def unfollow_user(db: Session, *, follower_id: str, target_id: str) -> None:
    follow = db.scalar(
        select(Follow).where(Follow.follower_id == follower_id, Follow.target_id == target_id)
    )
    if follow is None:
        return
    db.delete(follow)
    db.commit()


def decide_follow_request(
    db: Session,
    *,
    target_id: str,
    follow_id: uuid.UUID,
    accept: bool,
) -> Follow:
    follow = db.get(Follow, follow_id)
    if follow is None or follow.target_id != target_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Follow request not found")
    follow.status = FollowStatus.ACCEPTED if accept else FollowStatus.DECLINED
    follow.accepted_at = datetime.now(UTC) if accept else None
    db.commit()
    db.refresh(follow)
    return follow


def block_user(db: Session, *, blocker_id: str, blocked_id: str) -> UserBlock:
    if blocker_id == blocked_id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Cannot block self")
    block = UserBlock(blocker_id=blocker_id, blocked_id=blocked_id)
    db.add(block)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        existing = db.scalar(
            select(UserBlock).where(
                UserBlock.blocker_id == blocker_id,
                UserBlock.blocked_id == blocked_id,
            )
        )
        if existing is None:
            raise
        return existing
    db.refresh(block)
    return block


def unblock_user(db: Session, *, blocker_id: str, blocked_id: str) -> None:
    block = db.scalar(
        select(UserBlock).where(
            UserBlock.blocker_id == blocker_id,
            UserBlock.blocked_id == blocked_id,
        )
    )
    if block is None:
        return
    db.delete(block)
    db.commit()
