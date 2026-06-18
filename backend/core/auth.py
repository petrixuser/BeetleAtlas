import os
import secrets
from hashlib import sha256
from datetime import datetime, timedelta, timezone

import jwt
from fastapi import Depends, Header, HTTPException
from passlib.context import CryptContext

from backend.contracts.auth_contracts import AuthUserResponse
from backend.repositories.auth_repository import fetch_user_by_id


JWT_SECRET = os.getenv("JWT_SECRET", "change-me")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
JWT_ACCESS_TTL_MINUTES = int(os.getenv("JWT_ACCESS_TTL_MINUTES", "30"))
JWT_REFRESH_TTL_DAYS = int(os.getenv("JWT_REFRESH_TTL_DAYS", "14"))

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """Hash a plain-text password using bcrypt."""
    return _pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """Verify a plain-text password against a stored hash."""
    return _pwd_context.verify(password, password_hash)


def get_access_ttl_seconds() -> int:
    """Return configured access-token TTL in seconds."""
    return JWT_ACCESS_TTL_MINUTES * 60


def get_refresh_ttl_seconds() -> int:
    """Return configured refresh-token TTL in seconds."""
    return JWT_REFRESH_TTL_DAYS * 24 * 60 * 60


def get_refresh_expiry_utc() -> datetime:
    """Return UTC expiry timestamp for refresh tokens (naive for MySQL DATETIME)."""
    return (datetime.now(timezone.utc) + timedelta(seconds=get_refresh_ttl_seconds())).replace(tzinfo=None)


def generate_refresh_token() -> str:
    """Generate a high-entropy opaque refresh token."""
    return secrets.token_urlsafe(64)


def hash_refresh_token(refresh_token: str) -> str:
    """Hash refresh token for DB persistence and lookup."""
    return sha256(refresh_token.encode("utf-8")).hexdigest()


def create_access_token(subject: str, role: str) -> str:
    """Create a signed JWT access token for the given subject and role."""
    now = datetime.now(timezone.utc)
    payload = {
        "sub": subject,
        "role": role,
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(minutes=JWT_ACCESS_TTL_MINUTES)).timestamp()),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def _raise_unauthorized(message: str) -> None:
    raise HTTPException(
        status_code=401,
        detail={"error": "unauthorized", "message": message},
    )


def decode_access_token(token: str) -> dict:
    """Decode and validate a JWT access token payload."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.PyJWTError:
        _raise_unauthorized("Invalid access token.")

    sub = payload.get("sub")
    if sub is None:
        _raise_unauthorized("Invalid access token.")

    return payload


def to_auth_user_response(row: dict) -> AuthUserResponse:
    """Map DB row to AuthUserResponse contract."""
    return AuthUserResponse(
        id=int(row["user_id"]),
        email=row["email"],
        role=row["role"],
        is_active=bool(row["is_active"]),
        created_at=row["created_at"],
    )


def get_current_user(authorization: str | None = Header(default=None)) -> AuthUserResponse:
    """Resolve current user from Bearer token in Authorization header."""
    if not authorization or not authorization.lower().startswith("bearer "):
        _raise_unauthorized("Missing or invalid bearer token.")

    token = authorization.split(" ", 1)[1].strip()
    if not token:
        _raise_unauthorized("Missing or invalid bearer token.")

    payload = decode_access_token(token)

    try:
        user_id = int(payload["sub"])
    except (KeyError, TypeError, ValueError):
        _raise_unauthorized("Invalid access token.")

    user = fetch_user_by_id(user_id)
    if user is None or int(user.get("is_active") or 0) != 1:
        _raise_unauthorized("User is not authorized.")

    return to_auth_user_response(user)


def require_roles(*roles: str):
    """Return a dependency that enforces one of the allowed roles."""

    def _checker(current_user: AuthUserResponse = Depends(get_current_user)) -> AuthUserResponse:
        if current_user.role not in set(roles):
            raise HTTPException(
                status_code=403,
                detail={"error": "forbidden", "message": "Insufficient permissions."},
            )
        return current_user

    return _checker
