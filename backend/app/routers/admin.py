import logging

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.deps import get_db, require_admin
from app.core.security import ClerkUser
from app.schemas.admin import (
    AdminStatsResponse,
    RoleUpdateRequest,
    RoleUpdateResponse,
)
from app.services.admin import get_admin_stats, update_user_role

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/stats", response_model=AdminStatsResponse)
def admin_stats(
    db: Session = Depends(get_db),
    _: ClerkUser = Depends(require_admin),
    city: str = Query(default="Pune"),
) -> AdminStatsResponse:
    return get_admin_stats(db, city=city)


@router.patch("/users/{user_id}/role", response_model=RoleUpdateResponse)
def update_user_role_endpoint(
    user_id: str,
    payload: RoleUpdateRequest,
    _: ClerkUser = Depends(require_admin),
) -> RoleUpdateResponse:
    role = update_user_role(user_id, payload.role)
    return RoleUpdateResponse(user_id=user_id, role=role)
