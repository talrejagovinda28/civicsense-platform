import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict

from app.models.city import CityStatus


class CityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    slug: str
    name: str
    state_name: str
    state_code: str | None
    country_code: str
    status: CityStatus
    municipality_name: str | None
    center_lat: float
    center_lng: float
    default_zoom: int
    supports_reporting: bool
    supports_ward_map: bool
    supports_accountability: bool
    map_data_version: str | None
    created_at: datetime
    updated_at: datetime
