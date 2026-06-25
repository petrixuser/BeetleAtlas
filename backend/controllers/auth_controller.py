from datetime import datetime, timedelta, timezone
from typing import cast

from sqlalchemy.exc import IntegrityError

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
from backend.config.settings import (
    get_admin_bootstrap_token,
    get_email_verification_ttl_seconds,
    get_researcher_signup_code,
    is_admin_bootstrap_enabled,
    should_send_verification_email,
)
from backend.config.error_codes import ERR
from backend.controllers.core_controller import raise_api_error
from backend.core.auth import (
    create_access_token,
    get_access_ttl_seconds,
    get_refresh_expiry_utc,
    get_refresh_ttl_seconds,
    hash_refresh_token,
    hash_password,
    generate_refresh_token,
    to_auth_user_response,
    verify_password,
)
from backend.core.email_verification import send_verification_email
from backend.repositories.auth_repository import (
    fetch_active_refresh_token_by_hash,
    fetch_active_admin_user,
    fetch_refresh_token_by_hash,
    fetch_user_by_email,
    fetch_user_by_id,
    fetch_active_pending_registration_by_email,
    fetch_active_pending_registration_by_token_hash,
    insert_user,
    insert_refresh_token,
    revoke_refresh_token,
    revoke_user_refresh_tokens,
    consume_pending_registration,
    upsert_pending_registration,
    upsert_admin_user,
)


def _get_verification_expiry_utc(ttl_seconds: int):
    return (datetime.now(timezone.utc) + timedelta(seconds=ttl_seconds)).replace(tzinfo=None)


def register_controller(payload: RegisterRequest) -> RegisterPendingResponse:
    """Start registration and store a pending email-verification record."""
    email = payload.email.lower().strip()
    if not email:
        raise_api_error(400, ERR.AUTH.INVALID_EMAIL, "Email must not be empty.")

    existing = fetch_user_by_email(email)
    if existing is not None:
        raise_api_error(409, ERR.AUTH.EMAIL_EXISTS, "An account with this email already exists.")

    if payload.role == "admin":
        raise_api_error(403, ERR.COMMON.FORBIDDEN, "Admin registration is disabled.")

    if payload.role == "researcher":
        expected_code = get_researcher_signup_code()
        provided_code = (payload.researcher_signup_code or "").strip()
        if not expected_code:
            raise_api_error(503, ERR.AUTH.RESEARCHER_SIGNUP_UNAVAILABLE, "Researcher signup is not configured.")
        if provided_code != expected_code:
            raise_api_error(403, ERR.COMMON.FORBIDDEN, "Invalid researcher signup code.")

    password_hash = hash_password(payload.password)

    verification_token = generate_refresh_token()
    verification_token_hash = hash_refresh_token(verification_token)
    verification_ttl_seconds = get_email_verification_ttl_seconds()
    verification_expires_at = _get_verification_expiry_utc(verification_ttl_seconds)

    upsert_pending_registration(
        email=email,
        password_hash=password_hash,
        role=payload.role,
        token_hash=verification_token_hash,
        expires_at=verification_expires_at,
    )

    if should_send_verification_email():
        try:
            send_verification_email(email=email, verification_token=verification_token)
        except Exception:
            raise_api_error(503, ERR.AUTH.EMAIL_DELIVERY_FAILED, "Could not deliver verification email.")

    return RegisterPendingResponse(
        status="pending_verification",
        email=email,
        verification_token=verification_token,
        verification_expires_in=verification_ttl_seconds,
    )


def verify_email_controller(payload: VerifyEmailRequest) -> AuthUserResponse:
    """Verify token, create account, and activate it for login."""
    token_hash = hash_refresh_token(payload.verification_token)
    pending = fetch_active_pending_registration_by_token_hash(token_hash)
    if pending is None:
        raise_api_error(401, ERR.AUTH.INVALID_VERIFICATION_TOKEN, "Invalid or expired verification token.")
    pending_row = cast(dict, pending)

    email = str(pending_row["email"]).lower().strip()
    existing = fetch_user_by_email(email)
    if existing is not None:
        consume_pending_registration(int(pending_row["pending_registration_id"]))
        raise_api_error(409, ERR.AUTH.EMAIL_EXISTS, "An account with this email already exists.")

    created = None
    try:
        created = insert_user(
            email=email,
            password_hash=str(pending_row["password_hash"]),
            role=str(pending_row["role"]),
        )
    except IntegrityError:
        consume_pending_registration(int(pending_row["pending_registration_id"]))
        raise_api_error(409, ERR.AUTH.EMAIL_EXISTS, "An account with this email already exists.")

    consume_pending_registration(int(pending_row["pending_registration_id"]))

    if created is None:
        raise_api_error(500, ERR.AUTH.REGISTRATION_FAILED, "Could not create account.")

    return to_auth_user_response(cast(dict, created))


def login_controller(payload: LoginRequest) -> TokenResponse:
    """Authenticate user credentials and issue one access token."""
    email = payload.email.lower().strip()
    if not email:
        raise_api_error(400, ERR.AUTH.INVALID_EMAIL, "Email must not be empty.")

    user = fetch_user_by_email(email)
    if user is None:
        pending = fetch_active_pending_registration_by_email(email)
        if pending is not None:
            raise_api_error(403, ERR.AUTH.EMAIL_NOT_VERIFIED, "Email address is not verified yet.")
        raise_api_error(401, ERR.AUTH.INVALID_CREDENTIALS, "Invalid email or password.")
    user_row = cast(dict, user)

    if int(user_row.get("is_active") or 0) != 1:
        raise_api_error(403, ERR.AUTH.ACCOUNT_INACTIVE, "Account is inactive.")

    if not verify_password(payload.password, str(user_row.get("password_hash") or "")):
        raise_api_error(401, ERR.AUTH.INVALID_CREDENTIALS, "Invalid email or password.")

    access_token = create_access_token(subject=str(user_row["user_id"]), role=str(user_row["role"]))
    refresh_token = generate_refresh_token()
    refresh_token_hash = hash_refresh_token(refresh_token)
    refresh_expires_at = get_refresh_expiry_utc()
    insert_refresh_token(
        user_id=int(user_row["user_id"]),
        token_hash=refresh_token_hash,
        expires_at=refresh_expires_at,
    )

    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=get_access_ttl_seconds(),
        refresh_token=refresh_token,
        refresh_expires_in=get_refresh_ttl_seconds(),
    )


def refresh_controller(payload: RefreshRequest) -> TokenResponse:
    """Rotate refresh token and issue a new access token pair."""
    token_hash = hash_refresh_token(payload.refresh_token)
    stored = fetch_active_refresh_token_by_hash(token_hash)
    if stored is None:
        raise_api_error(401, ERR.AUTH.INVALID_REFRESH_TOKEN, "Invalid or expired refresh token.")
    stored_row = cast(dict, stored)

    user = fetch_user_by_id(int(stored_row["user_id"]))
    if user is None or int(user.get("is_active") or 0) != 1:
        raise_api_error(401, ERR.AUTH.INVALID_REFRESH_TOKEN, "Invalid or expired refresh token.")
    user_row = cast(dict, user)

    new_refresh_token = generate_refresh_token()
    new_refresh_hash = hash_refresh_token(new_refresh_token)
    new_refresh_expires_at = get_refresh_expiry_utc()
    new_refresh_id = insert_refresh_token(
        user_id=int(user_row["user_id"]),
        token_hash=new_refresh_hash,
        expires_at=new_refresh_expires_at,
    )

    revoke_refresh_token(
        refresh_token_id=int(stored_row["refresh_token_id"]),
        replaced_by_token_id=int(new_refresh_id),
    )

    access_token = create_access_token(subject=str(user_row["user_id"]), role=str(user_row["role"]))
    return TokenResponse(
        access_token=access_token,
        token_type="bearer",
        expires_in=get_access_ttl_seconds(),
        refresh_token=new_refresh_token,
        refresh_expires_in=get_refresh_ttl_seconds(),
    )


def logout_controller(current_user: AuthUserResponse, payload: LogoutRequest | None = None) -> LogoutResponse:
    """Revoke refresh token(s) and return logout acknowledgement."""
    refresh_token = None if payload is None else payload.refresh_token
    if refresh_token:
        token_hash = hash_refresh_token(refresh_token)
        row = fetch_refresh_token_by_hash(token_hash)
        if row is not None and int(row.get("user_id") or 0) == int(current_user.id):
            revoke_refresh_token(refresh_token_id=int(row["refresh_token_id"]))
    else:
        revoke_user_refresh_tokens(user_id=current_user.id)

    return LogoutResponse(status="ok")


def bootstrap_admin_controller(payload: BootstrapAdminRequest, bootstrap_token: str | None) -> AuthUserResponse:
    """Bootstrap first admin account for dev/setup using a shared secret."""
    if not is_admin_bootstrap_enabled():
        raise_api_error(404, ERR.COMMON.NOT_FOUND, "Route not found.")

    expected_token = get_admin_bootstrap_token()
    if not expected_token:
        raise_api_error(503, ERR.AUTH.BOOTSTRAP_UNAVAILABLE, "Admin bootstrap is not configured.")

    provided = (bootstrap_token or "").strip()
    if provided != expected_token:
        raise_api_error(403, ERR.COMMON.FORBIDDEN, "Invalid bootstrap token.")

    email = payload.email.lower().strip()
    if not email:
        raise_api_error(400, ERR.AUTH.INVALID_EMAIL, "Email must not be empty.")

    existing_admin = fetch_active_admin_user()
    if existing_admin is not None and str(existing_admin.get("email", "")).lower() != email:
        raise_api_error(
            409,
            ERR.AUTH.ADMIN_EXISTS,
            "An active admin account already exists with a different email.",
        )

    password_hash = hash_password(payload.password)
    admin_row = upsert_admin_user(email=email, password_hash=password_hash)

    if admin_row is None:
        raise_api_error(500, ERR.AUTH.BOOTSTRAP_FAILED, "Could not bootstrap admin account.")

    return to_auth_user_response(cast(dict, admin_row))
