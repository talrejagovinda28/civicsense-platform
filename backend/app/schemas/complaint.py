import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.models.complaint import ComplaintStatus
from app.schemas.category import CategoryResponse
from app.schemas.complaint_status import StatusHistoryResponse
from app.schemas.external_submission import ExternalSubmissionResponse


class ComplaintImageResponse(BaseModel):
    id: uuid.UUID
    cloudinary_url: str
    sort_order: int

    model_config = {"from_attributes": True}


class ComplaintFeedItem(BaseModel):
    id: uuid.UUID
    title: str
    description: str
    status: ComplaintStatus
    category: CategoryResponse
    ward: str | None
    city: str
    images: list[ComplaintImageResponse]
    created_at: datetime
    public_latitude: float | None = None
    public_longitude: float | None = None
    electoral_ward_id: uuid.UUID | None = None
    category_id: uuid.UUID | None = None


class ComplaintDetail(BaseModel):
    id: uuid.UUID
    title: str
    description: str
    status: ComplaintStatus
    category: CategoryResponse
    ward: str | None
    city: str
    images: list[ComplaintImageResponse]
    created_at: datetime
    updated_at: datetime
    address: str | None = None
    latitude: float | None = None
    longitude: float | None = None
    google_place_id: str | None = None
    user_id: str | None = None
    ai_suggested_category_id: uuid.UUID | None = None
    ai_confidence: float | None = None
    status_history: list[StatusHistoryResponse] = Field(default_factory=list)
    electoral_ward_id: uuid.UUID | None = None
    department_id: uuid.UUID | None = None
    ward_office_id: uuid.UUID | None = None
    city_id: uuid.UUID | None = None
    public_latitude: float | None = None
    public_longitude: float | None = None
    external_submission: ExternalSubmissionResponse | None = None
    approximate_location_label: str | None = None


class PaginatedComplaints(BaseModel):
    items: list[ComplaintFeedItem]
    total: int
    skip: int = Field(ge=0)
    limit: int = Field(ge=1, le=100)
