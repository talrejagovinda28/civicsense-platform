import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ProvenanceInfo(BaseModel):
    source_url: str | None = None
    source_name: str | None = None
    verified_at: datetime | None = None
    notes: str | None = None


class OfficialSummary(BaseModel):
    full_name: str
    party: str | None = None
    seat_label: str
    reservation: str | None = None


class DepartmentSummary(BaseModel):
    id: uuid.UUID
    name: str
    slug: str


class WardOfficeSummary(BaseModel):
    id: uuid.UUID
    name: str
    slug: str


class ElectoralWardSummary(BaseModel):
    id: uuid.UUID
    ward_no: int
    name: str


class RoutingChannelSummary(BaseModel):
    id: uuid.UUID
    channel_type: str
    label: str
    value: str
    url: str | None = None
    is_official: bool = True
    notes: str | None = None
    provenance: ProvenanceInfo | None = None


class AccountabilityResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    city_slug: str
    municipality_name: str
    inside_supported_area: bool
    electoral_ward: ElectoralWardSummary | None = None
    ward_office: WardOfficeSummary | None = None
    department: DepartmentSummary | None = None
    elected_representatives: list[OfficialSummary] = Field(default_factory=list)
    routing_channels: list[RoutingChannelSummary] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    provenance: ProvenanceInfo | None = None
