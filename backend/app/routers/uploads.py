import hashlib
import logging
import time

from fastapi import APIRouter, Depends, HTTPException, status

from app.core.config import settings
from app.core.deps import get_current_user
from app.core.security import ClerkUser
from app.schemas.upload import CloudinarySignatureResponse

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/uploads", tags=["uploads"])


def _build_signature(timestamp: int, folder: str) -> str:
    params = f"folder={folder}&timestamp={timestamp}{settings.CLOUDINARY_API_SECRET}"
    return hashlib.sha1(params.encode("utf-8")).hexdigest()


@router.post("/cloudinary-signature", response_model=CloudinarySignatureResponse)
def create_cloudinary_signature(
    _: ClerkUser = Depends(get_current_user),
) -> CloudinarySignatureResponse:
    if not settings.cloudinary_configured:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Cloudinary is not configured on the server",
        )

    timestamp = int(time.time())
    folder = settings.CLOUDINARY_FOLDER
    signature = _build_signature(timestamp, folder)

    logger.info("Generated Cloudinary upload signature for folder %s", folder)
    return CloudinarySignatureResponse(
        cloud_name=settings.CLOUDINARY_CLOUD_NAME,
        api_key=settings.CLOUDINARY_API_KEY,
        timestamp=timestamp,
        signature=signature,
        folder=folder,
    )
