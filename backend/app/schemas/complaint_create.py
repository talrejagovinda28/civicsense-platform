import uuid

from pydantic import BaseModel, Field, field_validator


class ComplaintImageInput(BaseModel):
    cloudinary_url: str = Field(max_length=500)
    cloudinary_public_id: str = Field(min_length=1, max_length=255)
    sort_order: int = Field(default=0, ge=0, le=2)

    @field_validator("cloudinary_url")
    @classmethod
    def validate_url(cls, value: str) -> str:
        if not value.startswith("https://"):
            raise ValueError("Image URL must be an https Cloudinary URL")
        return value


class SuggestCategoryRequest(BaseModel):
    photo_urls: list[str] = Field(min_length=1, max_length=3)

    @field_validator("photo_urls")
    @classmethod
    def validate_photo_urls(cls, values: list[str]) -> list[str]:
        for url in values:
            if not url.startswith("https://"):
                raise ValueError("Each photo URL must be an https URL")
        return values


class SuggestCategoryResponse(BaseModel):
    category_id: uuid.UUID
    category_name: str
    confidence: float = Field(ge=0.0, le=1.0)


class ComplaintCreate(BaseModel):
    description: str = Field(min_length=20, max_length=2000)
    category_id: uuid.UUID
    latitude: float = Field(ge=-90, le=90)
    longitude: float = Field(ge=-180, le=180)
    google_place_id: str = Field(min_length=1, max_length=255)
    address: str = Field(min_length=1, max_length=500)
    images: list[ComplaintImageInput] = Field(min_length=1, max_length=3)
    title: str | None = Field(default=None, min_length=5, max_length=200)
    ward: str | None = Field(default=None, max_length=100)
    city: str = Field(default="Pune", max_length=100)
    ai_suggested_category_id: uuid.UUID | None = None
    ai_confidence: float | None = Field(default=None, ge=0.0, le=1.0)
