from fastapi import APIRouter, Depends

from app.core.deps import get_current_user
from app.core.security import ClerkUser
from app.schemas.user import UserResponse

router = APIRouter(tags=["users"])


@router.get("/me", response_model=UserResponse)
def get_me(current_user: ClerkUser = Depends(get_current_user)) -> UserResponse:
    return UserResponse(user_id=current_user.user_id, role=current_user.role)
