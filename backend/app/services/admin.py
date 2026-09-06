import logging

import httpx
from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.category import Category
from app.models.complaint import Complaint, ComplaintStatus
from app.schemas.admin import AdminStatsResponse, CountItem

logger = logging.getLogger(__name__)

ALLOWED_ROLES = {"citizen", "officer", "admin"}


def get_admin_stats(db: Session, *, city: str = "Pune") -> AdminStatsResponse:
    total = (
        db.scalar(
            select(func.count()).select_from(Complaint).where(Complaint.city == city)
        )
        or 0
    )

    status_rows = db.execute(
        select(Complaint.status, func.count())
        .where(Complaint.city == city)
        .group_by(Complaint.status)
        .order_by(Complaint.status)
    ).all()

    category_rows = db.execute(
        select(Category.name, func.count())
        .join(Complaint, Complaint.category_id == Category.id)
        .where(Complaint.city == city)
        .group_by(Category.name)
        .order_by(Category.name)
    ).all()

    by_status = [
        CountItem(label=ComplaintStatus(status).value, count=count)
        for status, count in status_rows
    ]
    by_category = [
        CountItem(label=name, count=count) for name, count in category_rows
    ]

    logger.info("Admin stats for %s: total=%d", city, total)
    return AdminStatsResponse(
        city=city,
        total=total,
        by_status=by_status,
        by_category=by_category,
    )


def update_user_role(user_id: str, role: str) -> str:
    if role not in ALLOWED_ROLES:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Invalid role",
        )

    if not settings.CLERK_SECRET_KEY:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Clerk secret key not configured",
        )

    response = httpx.patch(
        f"https://api.clerk.com/v1/users/{user_id}",
        headers={
            "Authorization": f"Bearer {settings.CLERK_SECRET_KEY}",
            "Content-Type": "application/json",
        },
        json={"public_metadata": {"role": role}},
        timeout=10.0,
    )

    if response.status_code == 404:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Clerk user not found",
        )

    if response.status_code >= 400:
        logger.warning("Clerk role update failed: %s", response.text)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Could not update user role in Clerk",
        )

    logger.info("Updated Clerk user %s role to %s", user_id, role)
    return role
