from __future__ import annotations

import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.schemas.accountability import AccountabilityResponse
from app.services.accountability import get_accountability

router = APIRouter(prefix="/cities", tags=["accountability"])


@router.get("/{slug}/accountability", response_model=AccountabilityResponse)
def resolve_accountability(
    slug: str,
    lat: float = Query(ge=-90, le=90),
    lng: float = Query(ge=-180, le=180),
    category_id: uuid.UUID = Query(),
    db: Session = Depends(get_db),
) -> AccountabilityResponse:
    try:
        return get_accountability(
            db,
            city_slug=slug,
            latitude=lat,
            longitude=lng,
            category_id=category_id,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
