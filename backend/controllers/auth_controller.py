from sqlalchemy.exc import IntegrityError

from backend.contracts.auth_contracts import (
    AuthUserResponse,
    BootstrapAdminRequest,
    LoginRequest,
    LogoutRequest,
    LogoutResponse,
    RefreshRequest,
    RegisterRequest,
    TokenResponse,
)
from backend.config.settings import (
    get_admin_bootstrap_token,
    get_researcher_signup_code,
    is_admin_bootstrap_enabled,
)
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
from backend.repositories.auth_repository import (
    fetch_active_refresh_token_by_hash,
    fetch_active_admin_user,
    fetch_refresh_token_by_hash,
    fetch_user_by_email,
    fetch_user_by_id,
    insert_user,
    insert_refresh_token,
    revoke_refresh_token,
    revoke_user_refresh_tokens,
    upsert_admin_user,
)


def register_controller(payload: RegisterRequest) -> AuthUserResponse:
    """Register one user account and return the created user profile."""
    email = payload.email.lower().strip()
    if not email:
        raise_api_error(400, "invalid_email", "Email must not be empty.")

    existing = fetch_user_by_email(email)
    if existing is not None:
        raise_api_error(409, "email_exists", "An account with this email already exists.")

    if payload.role == "admin":
        raise_api_error(403, "forbidden", "Admin registration is disabled.")

    if payload.role == "researcher":
        expected_code = get_researcher_signup_code()
        provided_code = (payload.researcher_signup_code or "").strip()
        if not expected_code:
            raise_api_error(503, "researcher_signup_unavailable", "Researcher signup is not configured.")
        if provided_code != expected_code:
            raise_api_error(403, "forbidden", "Invalid researcher signup code.")

    password_hash = hash_password(payload.password)

    try:
        created = insert_user(email=email, password_hash=password_hash, role=payload.role)
    except IntegrityError:
        raise_api_error(409, "email_exists", "An account with this email already exists.")

    if created is None:
        raise_api_error(500, "registration_failed", "Could not create account.")

    return to_auth_user_response(created)


def login_controller(payload: LoginRequest) -> TokenResponse:
    """Authenticate user credentials and issue one access token."""
    email = payload.email.lower().strip()
    if not email:
        raise_api_error(400, "invalid_email", "Email must not be empty.")

    user = fetch_user_by_email(email)
    if user is None:
        raise_api_error(401, "invalid_credentials", "Invalid email or password.")

    if int(user.get("is_active") or 0) != 1:
        raise_api_error(403, "account_inactive", "Account is inactive.")

    if not verify_password(payload.password, str(user.get("password_hash") or "")):
        raise_api_error(401, "invalid_credentials", "Invalid email or password.")

    access_token = create_access_token(subject=str(user["user_id"]), role=str(user["role"]))
    refresh_token = generate_refresh_token()
    refresh_token_hash = hash_refresh_token(refresh_token)
    refresh_expires_at = get_refresh_expiry_utc()
    insert_refresh_token(
        user_id=int(user["user_id"]),
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
        raise_api_error(401, "invalid_refresh_token", "Invalid or expired refresh token.")

    user = fetch_user_by_id(int(stored["user_id"]))
    if user is None or int(user.get("is_active") or 0) != 1:
        raise_api_error(401, "invalid_refresh_token", "Invalid or expired refresh token.")

    new_refresh_token = generate_refresh_token()
    new_refresh_hash = hash_refresh_token(new_refresh_token)
    new_refresh_expires_at = get_refresh_expiry_utc()
    new_refresh_id = insert_refresh_token(
        user_id=int(user["user_id"]),
        token_hash=new_refresh_hash,
        expires_at=new_refresh_expires_at,
    )

    revoke_refresh_token(
        refresh_token_id=int(stored["refresh_token_id"]),
        replaced_by_token_id=int(new_refresh_id),
    )

    access_token = create_access_token(subject=str(user["user_id"]), role=str(user["role"]))
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
        raise_api_error(404, "not_found", "Route not found.")

    expected_token = get_admin_bootstrap_token()
    if not expected_token:
        raise_api_error(503, "bootstrap_unavailable", "Admin bootstrap is not configured.")

    provided = (bootstrap_token or "").strip()
    if provided != expected_token:
        raise_api_error(403, "forbidden", "Invalid bootstrap token.")

    email = payload.email.lower().strip()
    if not email:
        raise_api_error(400, "invalid_email", "Email must not be empty.")

    existing_admin = fetch_active_admin_user()
    if existing_admin is not None and str(existing_admin.get("email", "")).lower() != email:
        raise_api_error(
            409,
            "admin_exists",
            "An active admin account already exists with a different email.",
        )

    password_hash = hash_password(payload.password)
    admin_row = upsert_admin_user(email=email, password_hash=password_hash)

    if admin_row is None:
        raise_api_error(500, "bootstrap_failed", "Could not bootstrap admin account.")

    return to_auth_user_response(admin_row)
