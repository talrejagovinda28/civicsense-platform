from __future__ import annotations

import uuid

from sqlalchemy import select
from sqlalchemy.orm import Session, joinedload

from app.models.category import Category
from app.models.city import City
from app.models.electoral_ward import ElectoralWard
from app.models.public_official import OfficialJurisdiction, PublicOfficial
from app.models.routing import CategoryRoutingRule, Department, RoutingChannel
from app.models.ward_jurisdiction_mapping import WardJurisdictionMapping
from app.schemas.accountability import (
    AccountabilityResponse,
    DepartmentSummary,
    ElectoralWardSummary,
    OfficialSummary,
    ProvenanceInfo,
    RoutingChannelSummary,
    WardOfficeSummary,
)
from app.services.jurisdiction import resolve_electoral_ward

PMC_ENV_REPORT_SOURCE = (
    "https://www.pmc.gov.in/en/b/environment-status-report"
)


def get_accountability(
    db: Session,
    *,
    city_slug: str,
    latitude: float,
    longitude: float,
    category_id: uuid.UUID,
) -> AccountabilityResponse:
    city = db.scalar(select(City).where(City.slug == city_slug))
    if city is None:
        raise ValueError("City not found")
    if not city.supports_accountability:
        raise ValueError("Accountability data is not active for this city")

    category = db.scalar(
        select(Category).where(Category.id == category_id, Category.is_active.is_(True))
    )
    if category is None:
        raise ValueError("Category not found")

    ward, ward_message = resolve_electoral_ward(
        db,
        city_slug=city_slug,
        latitude=latitude,
        longitude=longitude,
    )
    warnings: list[str] = []
    if ward is None:
        return AccountabilityResponse(
            city_slug=city.slug,
            municipality_name=city.municipality_name or city.name,
            inside_supported_area=False,
            warnings=[ward_message or "Location is outside supported area."],
        )

    department = db.scalar(
        select(Department)
        .join(CategoryRoutingRule, CategoryRoutingRule.department_id == Department.id)
        .where(
            CategoryRoutingRule.city_id == city.id,
            CategoryRoutingRule.category_id == category.id,
        )
    )
    if department is None:
        warnings.append("No verified department mapping exists for this category yet.")

    mapping = db.scalar(
        select(WardJurisdictionMapping)
        .options(joinedload(WardJurisdictionMapping.ward_office))
        .where(WardJurisdictionMapping.electoral_ward_id == ward.id)
    )
    ward_office_summary = None
    if mapping and mapping.ward_office:
        ward_office_summary = WardOfficeSummary(
            id=mapping.ward_office.id,
            name=mapping.ward_office.name,
            slug=mapping.ward_office.slug,
        )
    else:
        warnings.append("Local ward office mapping is being verified.")

    jurisdictions = db.scalars(
        select(OfficialJurisdiction)
        .options(joinedload(OfficialJurisdiction.official))
        .where(OfficialJurisdiction.electoral_ward_id == ward.id)
        .order_by(OfficialJurisdiction.seat_label)
    ).all()

    representatives = [
        OfficialSummary(
            full_name=jurisdiction.official.full_name,
            party=jurisdiction.official.party,
            seat_label=jurisdiction.seat_label,
            reservation=jurisdiction.reservation,
        )
        for jurisdiction in jurisdictions
        if jurisdiction.official is not None
    ]

    channels = db.scalars(
        select(RoutingChannel)
        .where(
            RoutingChannel.city_id == city.id,
            RoutingChannel.is_active.is_(True),
        )
        .order_by(RoutingChannel.label)
    ).all()

    return AccountabilityResponse(
        city_slug=city.slug,
        municipality_name=city.municipality_name or city.name,
        inside_supported_area=True,
        electoral_ward=ElectoralWardSummary(
            id=ward.id,
            ward_no=ward.ward_no,
            name=ward.name,
        ),
        ward_office=ward_office_summary,
        department=(
            DepartmentSummary(
                id=department.id,
                name=department.name,
                slug=department.slug,
            )
            if department
            else None
        ),
        elected_representatives=representatives,
        routing_channels=[
            RoutingChannelSummary(
                id=channel.id,
                channel_type=channel.channel_type,
                label=channel.label,
                value=channel.value,
                url=channel.url,
                is_official=channel.is_official,
                notes=channel.notes,
                provenance=ProvenanceInfo(
                    source_url=channel.source_url,
                    verified_at=channel.verified_at,
                    notes=channel.notes,
                ),
            )
            for channel in channels
        ],
        warnings=warnings,
        provenance=ProvenanceInfo(
            source_url=ward.source_url,
            source_name="OpenCity PMC Electoral Wards 2025",
            verified_at=ward.verified_at,
            notes="Operational department routing uses PMC public reporting references.",
        ),
    )


def resolve_jurisdiction_for_complaint(
    db: Session,
    *,
    city_slug: str,
    latitude: float | None,
    longitude: float | None,
    category_id: uuid.UUID,
) -> dict:
    """Return IDs to persist on complaint create."""
    city = db.scalar(select(City).where(City.slug == city_slug))
    if city is None or not city.supports_reporting:
        raise ValueError("Reporting is not enabled for this city")

    result = {
        "city_id": city.id,
        "electoral_ward_id": None,
        "ward_office_id": None,
        "department_id": None,
        "ward_label": None,
    }

    if latitude is None or longitude is None:
        return result

    ward, message = resolve_electoral_ward(
        db,
        city_slug=city_slug,
        latitude=latitude,
        longitude=longitude,
    )
    if ward is None:
        raise ValueError(message or "Location is outside supported Pune area.")

    result["electoral_ward_id"] = ward.id
    result["ward_label"] = ward.name

    department = db.scalar(
        select(Department.id)
        .join(CategoryRoutingRule, CategoryRoutingRule.department_id == Department.id)
        .where(
            CategoryRoutingRule.city_id == city.id,
            CategoryRoutingRule.category_id == category_id,
        )
    )
    result["department_id"] = department

    mapping = db.scalar(
        select(WardJurisdictionMapping).where(
            WardJurisdictionMapping.electoral_ward_id == ward.id,
            WardJurisdictionMapping.confidence == "verified",
        )
    )
    if mapping:
        result["ward_office_id"] = mapping.ward_office_id

    return result
