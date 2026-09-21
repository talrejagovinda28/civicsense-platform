import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class DirectChatRequest(BaseModel):
    recipient_id: str = Field(min_length=1)


class DirectChatResponse(BaseModel):
    type: str
    conversation_id: uuid.UUID | None = None
    request_id: uuid.UUID | None = None
    status: str | None = None


class RequestDecideBody(BaseModel):
    decision: str = Field(pattern="^(accept|decline|block)$")


class MessageCreateRequest(BaseModel):
    body: str = Field(min_length=1, max_length=4000)


class ChatMessage(BaseModel):
    id: uuid.UUID
    chat_id: uuid.UUID
    sender_handle: str
    sender_display_name: str
    body: str
    created_at: datetime


class MessageListResponse(BaseModel):
    items: list[ChatMessage]
    next_cursor: str | None = None


class GroupCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    visibility: str = "private"


class ChatSummary(BaseModel):
    id: uuid.UUID
    title: str
    kind: str
    last_message_preview: str | None = None
    last_message_at: datetime | None = None
    unread_count: int = 0


class ConversationResponse(BaseModel):
    id: uuid.UUID
    type: str
    name: str | None
    created_by: str
    visibility: str
    created_at: datetime

    model_config = {"from_attributes": True}


class MessageResponse(BaseModel):
    id: uuid.UUID
    conversation_id: uuid.UUID
    sender_id: str
    body: str
    created_at: datetime

    model_config = {"from_attributes": True}
