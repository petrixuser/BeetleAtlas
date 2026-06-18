from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, EmailStr, Field


UserRole = Literal["researcher", "admin", "viewer"]


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)
    role: UserRole = "viewer"
    researcher_signup_code: str | None = Field(default=None, min_length=4, max_length=128)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)


class BootstrapAdminRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=12, max_length=128)


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
