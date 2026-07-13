"""API-Router fuer Authentifizierung: Registrierung, E-Mail-Verifizierung,
Login, Token-Refresh, Logout, Profil und Admin-Bootstrap."""

from fastapi import APIRouter, Depends, Header

from backend.contracts.auth_contracts import (
    AuthUserResponse,
    BootstrapAdminRequest,
    LoginRequest,
    LogoutRequest,
    LogoutResponse,
    RegisterPendingResponse,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
    VerifyEmailRequest,
)
from backend.controllers.auth_controller import (
    bootstrap_admin_controller,
    login_controller,
    logout_controller,
    refresh_controller,
    register_controller,
    verify_email_controller,
)
from backend.core.auth import get_current_user
from backend.core.rate_limit import (
    auth_bootstrap_rate_limit,
    auth_login_rate_limit,
    auth_refresh_rate_limit,
    auth_register_rate_limit,
)


router = APIRouter()


@router.post("/auth/register", response_model=RegisterPendingResponse)
def register(payload: RegisterRequest, _: None = Depends(auth_register_rate_limit)):
    """Startet die Registrierung und gibt das Verifizierungs-Payload zurueck."""
    return register_controller(payload)


@router.post("/auth/verify-email", response_model=AuthUserResponse)
def verify_email(payload: VerifyEmailRequest):
    """Verifiziert den Registrierungs-Token und legt ein aktives Nutzerkonto an."""
    return verify_email_controller(payload)


@router.post("/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, _: None = Depends(auth_login_rate_limit)):
    """Authentifiziert einen Nutzer und stellt einen Access-Token aus."""
    return login_controller(payload)


@router.post("/auth/refresh", response_model=TokenResponse)
def refresh(payload: RefreshRequest, _: None = Depends(auth_refresh_rate_limit)):
    """Rotiert den Refresh-Token und stellt ein neues Token-Paar aus."""
    return refresh_controller(payload)


@router.post("/auth/logout", response_model=LogoutResponse)
def logout(
    payload: LogoutRequest | None = None,
    current_user: AuthUserResponse = Depends(get_current_user),
):
    """Widerruft die Refresh-Token des aktuellen Nutzers."""
    return logout_controller(current_user, payload)


@router.get("/auth/me", response_model=AuthUserResponse)
def me(current_user: AuthUserResponse = Depends(get_current_user)):
    """Gibt das Profil des authentifizierten Nutzers zurueck."""
    return current_user


@router.post("/auth/bootstrap-admin", response_model=AuthUserResponse)
def bootstrap_admin(
    payload: BootstrapAdminRequest,
    bootstrap_token: str | None = Header(default=None, alias="X-Bootstrap-Token"),
    _: None = Depends(auth_bootstrap_rate_limit),
):
    """Legt das erste Admin-Konto fuer Dev/Setup mit einem gemeinsamen Geheimnis an."""
    return bootstrap_admin_controller(payload=payload, bootstrap_token=bootstrap_token)
