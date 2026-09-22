import logging
from dataclasses import dataclass

import jwt
from fastapi import HTTPException, status
from jwt import PyJWKClient

from app.core.config import settings

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class ClerkUser:
    user_id: str
    role: str


_jwks_client: PyJWKClient | None = None


def _get_jwks_client() -> PyJWKClient:
    global _jwks_client
    if _jwks_client is None:
        _jwks_client = PyJWKClient(settings.CLERK_JWKS_URL)
    return _jwks_client


def _role_from_payload(payload: dict) -> str:
    """Clerk session JWTs expose role via JWT template claims; support common shapes."""
    for key in ("role", "org_role"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip().lower()

    metadata = payload.get("metadata")
    if isinstance(metadata, dict):
        value = metadata.get("role")
        if isinstance(value, str) and value.strip():
            return value.strip().lower()

    public_metadata = payload.get("public_metadata")
    if isinstance(public_metadata, dict):
        value = public_metadata.get("role")
        if isinstance(value, str) and value.strip():
            return value.strip().lower()

    return "citizen"


def verify_clerk_token(token: str) -> ClerkUser:
    try:
        signing_key = _get_jwks_client().get_signing_key_from_jwt(token)
        decode_kwargs: dict = {
            "algorithms": ["RS256"],
            "options": {"verify_aud": False},
        }
        # Optional issuer pin — set CLERK_ISSUER in production to the Frontend API URL
        # (e.g. https://<slug>.clerk.accounts.dev) to reject tokens from other instances.
        issuer = getattr(settings, "CLERK_ISSUER", "") or ""
        if issuer.strip():
            decode_kwargs["issuer"] = issuer.strip()
        payload = jwt.decode(token, signing_key.key, **decode_kwargs)
    except jwt.PyJWTError as exc:
        # Do not log token contents or JWKS URLs with secrets.
        logger.warning("Clerk token verification failed: %s", type(exc).__name__)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        ) from exc

    user_id = payload.get("sub")
    if not user_id or not isinstance(user_id, str):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload",
        )

    return ClerkUser(user_id=user_id, role=_role_from_payload(payload))
