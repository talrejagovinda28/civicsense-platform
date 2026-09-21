import uuid
from datetime import datetime

from pydantic import BaseModel


class FeedItem(BaseModel):
    id: uuid.UUID
    kind: str
    title: str
    caption: str
    status: str
    ward: str | None
    city: str
    category_id: uuid.UUID
    public_latitude: float | None = None
    public_longitude: float | None = None
    created_at: datetime
    published_at: datetime
    image_count: int = 0
    thumbnail_url: str | None = None
    feed_event_id: uuid.UUID | None = None


class FeedResponse(BaseModel):
    items: list[FeedItem]
    next_cursor: str | None = None
