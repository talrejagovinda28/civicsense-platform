import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class FeedItem(BaseModel):
    id: uuid.UUID
    complaint_id: uuid.UUID
    kind: str
    title: str
    description: str | None = None
    status: str
    category_name: str | None = None
    locality_label: str | None = None
    responsibility_line: str = "Responsibility being verified"
    image_url: str | None = None
    thumbnail_url: str | None = None
    like_count: int = 0
    affected_count: int = 0
    comment_count: int = 0
    viewer_liked: bool = False
    viewer_affected: bool = False
    created_at: datetime
    published_at: datetime


class FeedResponse(BaseModel):
    items: list[FeedItem]
    next_cursor: str | None = None
