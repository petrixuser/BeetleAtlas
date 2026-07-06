from datetime import datetime
from typing import Literal
import re

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


UserRole = Literal["researcher", "admin", "viewer"]


def _validate_strong_password(value: str) -> str:
    if not re.search(r"[A-Z]", value):
        raise ValueError("password must contain at least one uppercase letter")
    if not re.search(r"[a-z]", value):
        raise ValueError("password must contain at least one lowercase letter")
    if not re.search(r"\d", value):
        raise ValueError("password must contain at least one digit")
    if not re.search(r"[^A-Za-z0-9]", value):
        raise ValueError("password must contain at least one special character")
    return value


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)
    role: UserRole = "viewer"
    researcher_signup_code: str | None = Field(default=None, min_length=4, max_length=128)

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        return _validate_strong_password(value)


class RegisterPendingResponse(BaseModel):
    status: Literal["pending_verification"] = "pending_verification"
    email: EmailStr
    verification_token: str | None = None
    email_sent: bool = False
    verification_expires_in: int


class VerifyEmailRequest(BaseModel):
    verification_token: str = Field(min_length=16, max_length=2048)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class BootstrapAdminRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)

    @field_validator("password")
    @classmethod
    def validate_password(cls, value: str) -> str:
        return _validate_strong_password(value)


class RefreshRequest(BaseModel):
    refresh_token: str = Field(min_length=16, max_length=2048)


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int
    refresh_token: str
    refresh_expires_in: int


class LogoutRequest(BaseModel):
    refresh_token: str | None = Field(default=None, min_length=16, max_length=2048)


class LogoutResponse(BaseModel):
    status: str = "ok"


class AuthUserResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: int
    email: EmailStr
    role: UserRole
    is_active: bool
    created_at: datetime = Field(alias="createdAt")
