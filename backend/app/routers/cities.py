import logging

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import JSONResponse
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.models.city import City
from app.models.electoral_ward import ElectoralWard
from app.schemas.city import CityResponse
from app.schemas.electoral_ward import ElectoralWardResponse, WardResolutionResponse
from app.services.jurisdiction import get_city_geojson, resolve_electoral_ward

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/cities", tags=["cities"])


@router.get("", response_model=list[CityResponse])
def list_cities(db: Session = Depends(get_db)) -> list[CityResponse]:
    stmt = select(City).order_by(City.name)
    cities = db.scalars(stmt).all()
    logger.info("Listed %d cities", len(cities))
    return cities


@router.get("/{slug}", response_model=CityResponse)
def get_city(slug: str, db: Session = Depends(get_db)) -> CityResponse:
    city = db.scalar(select(City).where(City.slug == slug))
    if city is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="City not found")
    return city


@router.get("/{slug}/wards", response_model=list[ElectoralWardResponse])
def list_city_wards(slug: str, db: Session = Depends(get_db)) -> list[ElectoralWardResponse]:
    city = db.scalar(select(City).where(City.slug == slug))
    if city is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="City not found")
    stmt = (
        select(ElectoralWard)
        .where(ElectoralWard.city_id == city.id)
        .order_by(ElectoralWard.ward_no)
    )
    return db.scalars(stmt).all()


@router.get("/{slug}/wards/geojson")
def get_city_wards_geojson(slug: str, db: Session = Depends(get_db)) -> JSONResponse:
    city = db.scalar(select(City).where(City.slug == slug))
    if city is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="City not found")
    if not city.supports_ward_map:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Ward map data is not available for this city",
        )
    payload = get_city_geojson(slug)
    return JSONResponse(
        content=payload,
        headers={"Cache-Control": "public, max-age=3600"},
    )


@router.get("/{slug}/wards/resolve", response_model=WardResolutionResponse)
def resolve_ward_for_point(
    slug: str,
    lat: float = Query(ge=-90, le=90),
    lng: float = Query(ge=-180, le=180),
    db: Session = Depends(get_db),
) -> WardResolutionResponse:
    city = db.scalar(select(City).where(City.slug == slug))
    if city is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="City not found")
    ward, message = resolve_electoral_ward(db, city_slug=slug, latitude=lat, longitude=lng)
    return WardResolutionResponse(
        inside_city=ward is not None,
        electoral_ward=ward,
        message=message,
    )
