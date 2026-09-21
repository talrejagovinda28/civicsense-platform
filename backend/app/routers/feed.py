from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_db, get_optional_user
from app.core.security import ClerkUser
from app.schemas.feed import FeedResponse
from app.services.feed import build_feed

router = APIRouter(prefix="/feed", tags=["feed"])


@router.get("", response_model=FeedResponse)
def get_feed(
    city: str = Query(default="pune", alias="city"),
    mode: str = Query(default="blend"),
    cursor: str | None = None,
    lat: float | None = None,
    lng: float | None = None,
    limit: int = Query(default=30, ge=1, le=50),
    db: Session = Depends(get_db),
    viewer: ClerkUser | None = Depends(get_optional_user),
) -> FeedResponse:
    result = build_feed(
        db,
        city_slug=city,
        mode=mode,
        cursor=cursor,
        lat=lat,
        lng=lng,
        limit=limit,
        viewer_id=viewer.user_id if viewer else None,
    )
    return FeedResponse(**result)
