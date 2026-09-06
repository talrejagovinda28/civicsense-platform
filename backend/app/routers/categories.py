import logging

from fastapi import APIRouter, Depends
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.models.category import Category
from app.schemas.category import CategoryResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/categories", tags=["categories"])


@router.get("", response_model=list[CategoryResponse])
def list_categories(db: Session = Depends(get_db)) -> list[CategoryResponse]:
    stmt = select(Category).where(Category.is_active.is_(True)).order_by(Category.name)
    categories = db.scalars(stmt).all()
    logger.info("Listed %d active categories", len(categories))
    return categories
