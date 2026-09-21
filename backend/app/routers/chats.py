import uuid

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_current_user, get_db
from app.core.security import ClerkUser
from app.schemas.messaging import (
    ChatMessage,
    ChatSummary,
    ConversationResponse,
    DirectChatRequest,
    DirectChatResponse,
    GroupCreateRequest,
    MessageCreateRequest,
    MessageListResponse,
    RequestDecideBody,
)
from app.services import messaging as messaging_service

router = APIRouter(prefix="/chats", tags=["chats"])


@router.get("", response_model=list[ChatSummary])
def list_chats(
    db: Session = Depends(get_db),
    current_user: ClerkUser = Depends(get_current_user),
) -> list[ChatSummary]:
    summaries = messaging_service.list_chat_summaries(db, user_id=current_user.user_id)
    return [ChatSummary(**summary) for summary in summaries]


@router.post("/direct", response_model=DirectChatResponse)
def create_direct_chat(
    payload: DirectChatRequest,
    db: Session = Depends(get_db),
    current_user: ClerkUser = Depends(get_current_user),
) -> DirectChatResponse:
    result = messaging_service.create_direct(
        db, sender_id=current_user.user_id, recipient_id=payload.recipient_id
    )
    return DirectChatResponse(**result)


@router.post("/requests/{request_id}/decide")
def decide_chat_request(
    request_id: uuid.UUID,
    payload: RequestDecideBody,
    db: Session = Depends(get_db),
    current_user: ClerkUser = Depends(get_current_user),
) -> dict:
    return messaging_service.decide_request(
        db,
        recipient_id=current_user.user_id,
        request_id=request_id,
        decision=payload.decision,
    )


@router.get("/{conversation_id}/messages", response_model=MessageListResponse)
def list_chat_messages(
    conversation_id: uuid.UUID,
    cursor: str | None = None,
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: ClerkUser = Depends(get_current_user),
) -> MessageListResponse:
    result = messaging_service.list_messages(
        db,
        user_id=current_user.user_id,
        conversation_id=conversation_id,
        cursor=cursor,
        limit=limit,
    )
    return MessageListResponse(
        items=[ChatMessage(**item) for item in result["items"]],
        next_cursor=result["next_cursor"],
    )


@router.post("/{conversation_id}/messages", response_model=ChatMessage)
def post_chat_message(
    conversation_id: uuid.UUID,
    payload: MessageCreateRequest,
    db: Session = Depends(get_db),
    current_user: ClerkUser = Depends(get_current_user),
) -> ChatMessage:
    message = messaging_service.post_message(
        db,
        user_id=current_user.user_id,
        conversation_id=conversation_id,
        body=payload.body,
    )
    return ChatMessage(**messaging_service.message_to_chat_item(db, message))


@router.post("/groups", response_model=ConversationResponse)
def create_group_chat(
    payload: GroupCreateRequest,
    db: Session = Depends(get_db),
    current_user: ClerkUser = Depends(get_current_user),
) -> ConversationResponse:
    return ConversationResponse.model_validate(
        messaging_service.create_group(
            db,
            creator_id=current_user.user_id,
            name=payload.name,
            visibility=payload.visibility,
        )
    )


@router.post("/{conversation_id}/join")
def join_group_chat(
    conversation_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: ClerkUser = Depends(get_current_user),
) -> dict:
    member = messaging_service.join_group(
        db, user_id=current_user.user_id, conversation_id=conversation_id
    )
    return {"conversation_id": member.conversation_id, "user_id": member.user_id}
