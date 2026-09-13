import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ElectoralWardResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    city_id: uuid.UUID
    external_code: str | None
    ward_no: int
    name: str
    geometry_feature_id: str
    source_url: str | None
    source_license: str | None
    verified_at: datetime | None


class WardResolutionResponse(BaseModel):
    inside_city: bool
    electoral_ward: ElectoralWardResponse | None
    message: str | None = None
