import os
from typing import List

"""This module contains configuration settings for the backend application, including database connection details and allowed origins for CORS."""
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


def get_redis_url() -> str:
    """Return Redis connection URL for distributed rate limiting."""
    return os.getenv("REDIS_URL", "").strip()
