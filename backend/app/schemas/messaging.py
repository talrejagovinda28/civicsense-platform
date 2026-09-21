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


class MessageResponse(BaseModel):
    id: uuid.UUID
    conversation_id: uuid.UUID
    sender_id: str
    body: str
    created_at: datetime

    model_config = {"from_attributes": True}


class MessageListResponse(BaseModel):
    items: list[MessageResponse]
    next_cursor: str | None = None


class GroupCreateRequest(BaseModel):
    name: str = Field(min_length=1, max_length=200)
    visibility: str = "private"


class ConversationResponse(BaseModel):
    id: uuid.UUID
    type: str
    name: str | None
    created_by: str
    visibility: str
    created_at: datetime

    model_config = {"from_attributes": True}
