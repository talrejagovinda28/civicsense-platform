from __future__ import annotations

import uuid
from datetime import UTC, datetime

from fastapi import HTTPException, status
from sqlalchemy import and_, func, or_, select
from sqlalchemy.orm import Session, joinedload

from app.models.community import Follow, FollowStatus, UserBlock
from app.models.messaging import (
    Conversation,
    ConversationMember,
    ConversationType,
    ConversationVisibility,
    Message,
    MessageRead,
    MessageRequest,
    MessageRequestStatus,
)
from app.models.user import DmPolicy, UserProfile
from app.services.reputation import can_create_group, can_initiate_dm


def _is_member(db: Session, conversation_id: uuid.UUID, user_id: str) -> bool:
    return (
        db.scalar(
            select(ConversationMember).where(
                ConversationMember.conversation_id == conversation_id,
                ConversationMember.user_id == user_id,
                ConversationMember.status == "active",
            )
        )
        is not None
    )


def _mutual_follow(db: Session, user_a: str, user_b: str) -> bool:
    a_to_b = db.scalar(
        select(Follow).where(
            Follow.follower_id == user_a,
            Follow.target_id == user_b,
            Follow.status == FollowStatus.ACCEPTED,
        )
    )
    b_to_a = db.scalar(
        select(Follow).where(
            Follow.follower_id == user_b,
            Follow.target_id == user_a,
            Follow.status == FollowStatus.ACCEPTED,
        )
    )
    return a_to_b is not None and b_to_a is not None


def _profile_for_user(db: Session, user_id: str) -> UserProfile | None:
    return db.scalar(select(UserProfile).where(UserProfile.clerk_user_id == user_id))


def _sender_identity(db: Session, sender_id: str) -> tuple[str, str]:
    profile = _profile_for_user(db, sender_id)
    if profile is not None:
        handle = profile.handle or f"user_{sender_id[:8]}"
        display_name = profile.display_name or handle
        return handle, display_name
    return f"user_{sender_id[:8]}", "Citizen"


def _conversation_kind(conversation_type: str) -> str:
    if conversation_type == ConversationType.DIRECT:
        return "direct"
    if conversation_type == ConversationType.ISSUE:
        return "issue"
    return "group"


def _conversation_title(db: Session, conversation: Conversation, user_id: str) -> str:
    if conversation.name:
        return conversation.name
    if conversation.type == ConversationType.DIRECT:
        other_ids = [
            member.user_id
            for member in conversation.members
            if member.user_id != user_id and member.status == "active"
        ]
        if other_ids:
            _, display_name = _sender_identity(db, other_ids[0])
            return display_name
        return "Direct chat"
    return "Group chat"


def _last_message(db: Session, conversation_id: uuid.UUID) -> Message | None:
    return db.scalar(
        select(Message)
        .where(
            Message.conversation_id == conversation_id,
            Message.deleted_at.is_(None),
        )
        .order_by(Message.created_at.desc(), Message.id.desc())
        .limit(1)
    )


def _unread_count(db: Session, *, conversation_id: uuid.UUID, user_id: str) -> int:
    read_state = db.scalar(
        select(MessageRead).where(
            MessageRead.conversation_id == conversation_id,
            MessageRead.user_id == user_id,
        )
    )
    stmt = select(func.count()).select_from(Message).where(
        Message.conversation_id == conversation_id,
        Message.deleted_at.is_(None),
        Message.sender_id != user_id,
    )
    if read_state is not None:
        stmt = stmt.where(Message.created_at > read_state.last_read_at)
    return int(db.scalar(stmt) or 0)


def list_chat_summaries(db: Session, *, user_id: str) -> list[dict]:
    conversations = list(
        db.scalars(
            select(Conversation)
            .join(ConversationMember)
            .where(
                ConversationMember.user_id == user_id,
                ConversationMember.status == "active",
            )
            .options(joinedload(Conversation.members))
            .order_by(Conversation.updated_at.desc())
        ).unique()
    )
    summaries: list[dict] = []
    for conversation in conversations:
        last_message = _last_message(db, conversation.id)
        preview = None
        last_at = None
        if last_message is not None:
            preview = last_message.body[:120]
            last_at = last_message.created_at
        summaries.append(
            {
                "id": conversation.id,
                "title": _conversation_title(db, conversation, user_id),
                "kind": _conversation_kind(conversation.type),
                "last_message_preview": preview,
                "last_message_at": last_at,
                "unread_count": _unread_count(
                    db, conversation_id=conversation.id, user_id=user_id
                ),
            }
        )
    return summaries


def list_conversations(db: Session, *, user_id: str) -> list[Conversation]:
    return list(
        db.scalars(
            select(Conversation)
            .join(ConversationMember)
            .where(
                ConversationMember.user_id == user_id,
                ConversationMember.status == "active",
            )
            .options(joinedload(Conversation.members))
            .order_by(Conversation.updated_at.desc())
        ).unique()
    )


def create_direct(
    db: Session,
    *,
    sender_id: str,
    recipient_id: str,
) -> dict:
    if sender_id == recipient_id:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid recipient")

    if not can_initiate_dm(db, sender_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Direct messaging requires {200} lifetime XP",
        )

    blocked = db.scalar(
        select(UserBlock).where(
            or_(
                and_(UserBlock.blocker_id == recipient_id, UserBlock.blocked_id == sender_id),
                and_(UserBlock.blocker_id == sender_id, UserBlock.blocked_id == recipient_id),
            )
        )
    )
    if blocked is not None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Blocked")

    recipient_profile = db.scalar(
        select(UserProfile).where(UserProfile.clerk_user_id == recipient_id)
    )
    if recipient_profile and recipient_profile.dm_policy == DmPolicy.NONE:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Recipient disallows DMs")

    if _mutual_follow(db, sender_id, recipient_id):
        conversation = Conversation(
            type=ConversationType.DIRECT,
            created_by=sender_id,
            visibility=ConversationVisibility.PRIVATE,
        )
        db.add(conversation)
        db.flush()
        for uid in (sender_id, recipient_id):
            db.add(
                ConversationMember(
                    conversation_id=conversation.id,
                    user_id=uid,
                    role="member",
                    status="active",
                )
            )
        db.commit()
        db.refresh(conversation)
        return {"type": "conversation", "conversation_id": conversation.id}

    existing_request = db.scalar(
        select(MessageRequest).where(
            MessageRequest.sender_id == sender_id,
            MessageRequest.recipient_id == recipient_id,
            MessageRequest.status == MessageRequestStatus.PENDING,
        )
    )
    if existing_request is not None:
        return {"type": "request", "request_id": existing_request.id, "status": "pending"}

    request = MessageRequest(
        sender_id=sender_id,
        recipient_id=recipient_id,
        status=MessageRequestStatus.PENDING,
    )
    db.add(request)
    db.commit()
    db.refresh(request)
    return {"type": "request", "request_id": request.id, "status": "pending"}


def decide_request(
    db: Session,
    *,
    recipient_id: str,
    request_id: uuid.UUID,
    decision: str,
) -> dict:
    request = db.get(MessageRequest, request_id)
    if request is None or request.recipient_id != recipient_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Request not found")

    if decision == "accept":
        request.status = MessageRequestStatus.ACCEPTED
        conversation = Conversation(
            type=ConversationType.DIRECT,
            created_by=request.sender_id,
            visibility=ConversationVisibility.PRIVATE,
        )
        db.add(conversation)
        db.flush()
        request.conversation_id = conversation.id
        for uid in (request.sender_id, request.recipient_id):
            db.add(
                ConversationMember(
                    conversation_id=conversation.id,
                    user_id=uid,
                    role="member",
                    status="active",
                )
            )
        db.commit()
        return {"status": "accepted", "conversation_id": conversation.id}

    if decision == "block":
        request.status = MessageRequestStatus.DECLINED
        db.add(UserBlock(blocker_id=recipient_id, blocked_id=request.sender_id))
        db.commit()
        return {"status": "blocked"}

    request.status = MessageRequestStatus.DECLINED
    db.commit()
    return {"status": "declined"}


def post_message(
    db: Session,
    *,
    user_id: str,
    conversation_id: uuid.UUID,
    body: str,
) -> Message:
    if not _is_member(db, conversation_id, user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member")

    message = Message(
        conversation_id=conversation_id,
        sender_id=user_id,
        body=body.strip(),
    )
    db.add(message)
    db.commit()
    db.refresh(message)
    return message


def message_to_chat_item(db: Session, message: Message) -> dict:
    handle, display_name = _sender_identity(db, message.sender_id)
    return {
        "id": message.id,
        "chat_id": message.conversation_id,
        "sender_handle": handle,
        "sender_display_name": display_name,
        "body": message.body,
        "created_at": message.created_at,
    }


def list_messages(
    db: Session,
    *,
    user_id: str,
    conversation_id: uuid.UUID,
    cursor: str | None = None,
    limit: int = 50,
) -> dict:
    if not _is_member(db, conversation_id, user_id):
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not a member")

    stmt = (
        select(Message)
        .where(
            Message.conversation_id == conversation_id,
            Message.deleted_at.is_(None),
        )
        .order_by(Message.created_at.asc(), Message.id.asc())
        .limit(limit + 1)
    )

    if cursor:
        cursor_created, cursor_id_str = cursor.split("|", 1)
        cursor_id = uuid.UUID(cursor_id_str)
        cursor_dt = datetime.fromisoformat(cursor_created)
        stmt = stmt.where(
            or_(
                Message.created_at > cursor_dt,
                and_(Message.created_at == cursor_dt, Message.id > cursor_id),
            )
        )

    messages = list(db.scalars(stmt))
    items = messages[:limit]
    next_cursor = None
    if len(messages) > limit:
        last = items[-1]
        next_cursor = f"{last.created_at.isoformat()}|{last.id}"
    chat_items = []
    for message in items:
        handle, display_name = _sender_identity(db, message.sender_id)
        chat_items.append(
            {
                "id": message.id,
                "chat_id": message.conversation_id,
                "sender_handle": handle,
                "sender_display_name": display_name,
                "body": message.body,
                "created_at": message.created_at,
            }
        )
    return {"items": chat_items, "next_cursor": next_cursor}


def create_group(
    db: Session,
    *,
    creator_id: str,
    name: str,
    visibility: str = "private",
) -> Conversation:
    if not can_create_group(db, creator_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Group creation requires 500 lifetime XP",
        )

    conversation = Conversation(
        type=ConversationType.GROUP,
        name=name.strip(),
        created_by=creator_id,
        visibility=visibility,
    )
    db.add(conversation)
    db.flush()
    db.add(
        ConversationMember(
            conversation_id=conversation.id,
            user_id=creator_id,
            role="owner",
            status="active",
        )
    )
    db.commit()
    db.refresh(conversation)
    return conversation


def join_group(
    db: Session,
    *,
    user_id: str,
    conversation_id: uuid.UUID,
) -> ConversationMember:
    conversation = db.get(Conversation, conversation_id)
    if conversation is None or conversation.type not in {
        ConversationType.LOCALITY,
        ConversationType.ISSUE,
        ConversationType.GROUP,
    }:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Group not found")
    if conversation.visibility != "public":
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Group is not joinable")

    if _is_member(db, conversation_id, user_id):
        member = db.scalar(
            select(ConversationMember).where(
                ConversationMember.conversation_id == conversation_id,
                ConversationMember.user_id == user_id,
            )
        )
        assert member is not None
        return member

    member = ConversationMember(
        conversation_id=conversation_id,
        user_id=user_id,
        role="member",
        status="active",
    )
    db.add(member)
    db.commit()
    db.refresh(member)
    return member
