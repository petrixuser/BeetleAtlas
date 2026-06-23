import os
from typing import List

"""This module contains configuration settings for the backend application, including database connection details and allowed origins for CORS."""


_WEAK_SECRET_VALUES = {
    "change-me",
    "changeme",
    "dev-secret",
    "secret",
    "password",
    "test",
}


def _is_weak_secret(value: str) -> bool:
    return value.strip().lower() in _WEAK_SECRET_VALUES


def _is_truthy(raw: str | None) -> bool:
    return (raw or "").strip().lower() in {"1", "true", "yes", "on"}


def validate_runtime_security() -> None:
    """Fail fast when critical auth/DB security environment is unsafe."""
    errors: list[str] = []

    jwt_secret = os.getenv("JWT_SECRET", "").strip()
    if not jwt_secret:
        errors.append("Missing required environment variable JWT_SECRET.")
    elif _is_weak_secret(jwt_secret):
        errors.append("JWT_SECRET is set to a weak placeholder value.")

    researcher_code = os.getenv("RESEARCHER_SIGNUP_CODE", "").strip()
    if not researcher_code:
        errors.append("Missing required environment variable RESEARCHER_SIGNUP_CODE.")
    elif _is_weak_secret(researcher_code):
        errors.append("RESEARCHER_SIGNUP_CODE is set to a weak placeholder value.")

    bootstrap_enabled = _is_truthy(os.getenv("ALLOW_ADMIN_BOOTSTRAP"))
    if bootstrap_enabled:
        bootstrap_token = os.getenv("ADMIN_BOOTSTRAP_TOKEN", "").strip()
        if not bootstrap_token:
            errors.append(
                "ALLOW_ADMIN_BOOTSTRAP is enabled but ADMIN_BOOTSTRAP_TOKEN is missing."
            )
        elif _is_weak_secret(bootstrap_token):
            errors.append("ADMIN_BOOTSTRAP_TOKEN is set to a weak placeholder value.")

    db_user = os.getenv("DB_USER", "").strip()
    db_password = os.getenv("DB_PASSWORD", "").strip()
    if not db_user:
        errors.append("Missing required environment variable DB_USER.")
    if not db_password:
        errors.append("Missing required environment variable DB_PASSWORD.")
    elif _is_weak_secret(db_password):
        errors.append("DB_PASSWORD is set to a weak placeholder value.")

    if db_user.lower() == "root":
        errors.append("DB_USER must not be root. Use a dedicated least-privilege app user.")

    if errors:
        raise RuntimeError("\n".join(errors))


def parse_allowed_origins() -> List[str]:
    raw_origins = os.getenv("FRONTEND_ORIGINS", "http://localhost:5173,http://localhost:8080")
    origins = [origin.strip() for origin in raw_origins.split(",") if origin.strip()]
    return origins or ["http://localhost:5173"]


def parse_bool_env(name: str, default: bool = False) -> bool:
    """Parse a boolean environment variable with sane defaults."""
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def is_admin_bootstrap_enabled() -> bool:
    """Return whether the admin bootstrap endpoint is enabled."""
    return parse_bool_env("ALLOW_ADMIN_BOOTSTRAP", False)


def get_admin_bootstrap_token() -> str:
    """Return required shared secret for admin bootstrap endpoint."""
    return os.getenv("ADMIN_BOOTSTRAP_TOKEN", "").strip()


def get_researcher_signup_code() -> str:
    """Return shared signup code required for researcher registration."""
    return os.getenv("RESEARCHER_SIGNUP_CODE", "").strip()


def parse_int_env(name: str, default: int) -> int:
    """Parse an integer environment variable and fall back to default."""
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw.strip())
    except ValueError:
        return default


def get_auth_register_rate_limit() -> tuple[int, int]:
    """Return (max_requests, window_seconds) for register endpoint."""
    max_requests = parse_int_env("AUTH_REGISTER_MAX_REQUESTS", 8)
    window_seconds = parse_int_env("AUTH_REGISTER_WINDOW_SECONDS", 300)
    return max(max_requests, 1), max(window_seconds, 1)


def get_auth_login_rate_limit() -> tuple[int, int]:
    """Return (max_requests, window_seconds) for login endpoint."""
    max_requests = parse_int_env("AUTH_LOGIN_MAX_REQUESTS", 20)
    window_seconds = parse_int_env("AUTH_LOGIN_WINDOW_SECONDS", 60)
    return max(max_requests, 1), max(window_seconds, 1)


def get_auth_refresh_rate_limit() -> tuple[int, int]:
    """Return (max_requests, window_seconds) for refresh endpoint."""
    max_requests = parse_int_env("AUTH_REFRESH_MAX_REQUESTS", 30)
    window_seconds = parse_int_env("AUTH_REFRESH_WINDOW_SECONDS", 60)
    return max(max_requests, 1), max(window_seconds, 1)


def get_auth_bootstrap_rate_limit() -> tuple[int, int]:
    """Return (max_requests, window_seconds) for bootstrap-admin endpoint."""
    max_requests = parse_int_env("AUTH_BOOTSTRAP_MAX_REQUESTS", 3)
    window_seconds = parse_int_env("AUTH_BOOTSTRAP_WINDOW_SECONDS", 600)
    return max(max_requests, 1), max(window_seconds, 1)


def get_email_verification_ttl_seconds() -> int:
    """Return validity period for email verification tokens in seconds."""
    ttl = parse_int_env("EMAIL_VERIFICATION_TTL_SECONDS", 86400)
    return max(ttl, 300)


def should_send_verification_email() -> bool:
    """Return whether registration should send verification emails via SMTP."""
    return parse_bool_env("EMAIL_VERIFICATION_SEND_EMAIL", False)


def get_email_verification_base_url() -> str:
    """Return public frontend/base URL used to build email verification links."""
    return os.getenv("EMAIL_VERIFICATION_BASE_URL", "http://localhost:8080").strip()


def get_smtp_host() -> str:
    return os.getenv("SMTP_HOST", "").strip()


def get_smtp_port() -> int:
    return parse_int_env("SMTP_PORT", 587)


def get_smtp_username() -> str:
    return os.getenv("SMTP_USERNAME", "").strip()


def get_smtp_password() -> str:
    return os.getenv("SMTP_PASSWORD", "").strip()


def get_smtp_from_email() -> str:
    return os.getenv("SMTP_FROM_EMAIL", "no-reply@beetleatlas.local").strip()


def use_smtp_starttls() -> bool:
    return parse_bool_env("SMTP_USE_STARTTLS", True)


def use_smtp_ssl() -> bool:
    return parse_bool_env("SMTP_USE_SSL", False)


def get_redis_url() -> str:
    """Return Redis connection URL for distributed rate limiting."""
    return os.getenv("REDIS_URL", "").strip()
