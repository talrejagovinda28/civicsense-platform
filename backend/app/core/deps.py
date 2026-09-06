from collections.abc import Generator

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.security import ClerkUser, verify_clerk_token
from app.db.session import SessionLocal

security = HTTPBearer()
optional_security = HTTPBearer(auto_error=False)


def get_db() -> Generator[Session, None, None]:
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> ClerkUser:
    return verify_clerk_token(credentials.credentials)


def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(optional_security),
) -> ClerkUser | None:
    if credentials is None:
        return None
    return verify_clerk_token(credentials.credentials)


def require_officer_or_admin(
    current_user: ClerkUser = Depends(get_current_user),
) -> ClerkUser:
    if current_user.role not in {"officer", "admin"}:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Officer or admin access required",
        )
    return current_user


def require_admin(
    current_user: ClerkUser = Depends(get_current_user),
) -> ClerkUser:
    if current_user.role != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required",
        )
    return current_user
