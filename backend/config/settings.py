"""Konfiguration der Backend-Anwendung: DB-Verbindung, CORS-Herkuenfte u. a."""
import os
from typing import List


_WEAK_SECRET_VALUES = {
    "change-me",
    "changeme",
    "dev-secret",
    "secret",
    "password",
    "test",
}


def _is_weak_secret(value: str) -> bool:
    """Prueft, ob der Wert einem schwachen Platzhalter-Secret entspricht."""
    return value.strip().lower() in _WEAK_SECRET_VALUES


def _is_truthy(raw: str | None) -> bool:
    """Prueft, ob ein Rohwert als 'wahr' (1/true/yes/on) zu interpretieren ist."""
    return (raw or "").strip().lower() in {"1", "true", "yes", "on"}


def validate_runtime_security() -> None:
    """Bricht frueh ab, wenn kritische Auth-/DB-Sicherheitsvariablen unsicher sind."""
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
    """Liest die erlaubten CORS-Herkuenfte aus FRONTEND_ORIGINS."""
    raw_origins = os.getenv("FRONTEND_ORIGINS", "http://localhost:5173,http://localhost:8080")
    origins = [origin.strip() for origin in raw_origins.split(",") if origin.strip()]
    return origins or ["http://localhost:5173"]


def parse_bool_env(name: str, default: bool = False) -> bool:
    """Liest eine boolesche Umgebungsvariable mit sinnvollen Vorgabewerten."""
    raw = os.getenv(name)
    if raw is None:
        return default
    return raw.strip().lower() in {"1", "true", "yes", "on"}


def is_admin_bootstrap_enabled() -> bool:
    """Gibt zurueck, ob der Admin-Bootstrap-Endpunkt aktiviert ist."""
    return parse_bool_env("ALLOW_ADMIN_BOOTSTRAP", False)


def get_admin_bootstrap_token() -> str:
    """Gibt das benoetigte Shared Secret (Token) fuer den Admin-Bootstrap-Endpunkt zurueck."""
    return os.getenv("ADMIN_BOOTSTRAP_TOKEN", "").strip()


def get_researcher_signup_code() -> str:
    """Gibt den fuer die Forscher-Registrierung benoetigten Signup-Code zurueck."""
    return os.getenv("RESEARCHER_SIGNUP_CODE", "").strip()


def parse_int_env(name: str, default: int) -> int:
    """Liest eine Ganzzahl-Umgebungsvariable und faellt auf den Vorgabewert zurueck."""
    raw = os.getenv(name)
    if raw is None:
        return default
    try:
        return int(raw.strip())
    except ValueError:
        return default


def get_auth_register_rate_limit() -> tuple[int, int]:
    """Gibt (max_requests, window_seconds) fuer den Register-Endpunkt zurueck."""
    max_requests = parse_int_env("AUTH_REGISTER_MAX_REQUESTS", 8)
    window_seconds = parse_int_env("AUTH_REGISTER_WINDOW_SECONDS", 300)
    return max(max_requests, 1), max(window_seconds, 1)


def get_auth_login_rate_limit() -> tuple[int, int]:
    """Gibt (max_requests, window_seconds) fuer den Login-Endpunkt zurueck."""
    max_requests = parse_int_env("AUTH_LOGIN_MAX_REQUESTS", 20)
    window_seconds = parse_int_env("AUTH_LOGIN_WINDOW_SECONDS", 60)
    return max(max_requests, 1), max(window_seconds, 1)


def get_auth_refresh_rate_limit() -> tuple[int, int]:
    """Gibt (max_requests, window_seconds) fuer den Refresh-Endpunkt zurueck."""
    max_requests = parse_int_env("AUTH_REFRESH_MAX_REQUESTS", 30)
    window_seconds = parse_int_env("AUTH_REFRESH_WINDOW_SECONDS", 60)
    return max(max_requests, 1), max(window_seconds, 1)


def get_auth_bootstrap_rate_limit() -> tuple[int, int]:
    """Gibt (max_requests, window_seconds) fuer den bootstrap-admin-Endpunkt zurueck."""
    max_requests = parse_int_env("AUTH_BOOTSTRAP_MAX_REQUESTS", 3)
    window_seconds = parse_int_env("AUTH_BOOTSTRAP_WINDOW_SECONDS", 600)
    return max(max_requests, 1), max(window_seconds, 1)


def get_email_verification_ttl_seconds() -> int:
    """Gibt die Gueltigkeitsdauer von E-Mail-Verifizierungs-Token in Sekunden zurueck."""
    ttl = parse_int_env("EMAIL_VERIFICATION_TTL_SECONDS", 86400)
    return max(ttl, 300)


def should_send_verification_email() -> bool:
    """Gibt zurueck, ob die Registrierung Verifizierungs-E-Mails per SMTP versenden soll."""
    return parse_bool_env("EMAIL_VERIFICATION_SEND_EMAIL", False)


def get_email_verification_base_url() -> str:
    """Gibt die oeffentliche Basis-URL zum Bau der E-Mail-Verifizierungslinks zurueck."""
    return os.getenv("EMAIL_VERIFICATION_BASE_URL", "http://localhost:8080").strip()


def get_smtp_host() -> str:
    """Gibt den SMTP-Host fuer den E-Mail-Versand zurueck."""
    return os.getenv("SMTP_HOST", "").strip()


def get_smtp_port() -> int:
    """Gibt den SMTP-Port fuer den E-Mail-Versand zurueck."""
    return parse_int_env("SMTP_PORT", 587)


def get_smtp_username() -> str:
    """Gibt den SMTP-Benutzernamen fuer die Authentifizierung zurueck."""
    return os.getenv("SMTP_USERNAME", "").strip()


def get_smtp_password() -> str:
    """Gibt das SMTP-Passwort fuer die Authentifizierung zurueck."""
    return os.getenv("SMTP_PASSWORD", "").strip()


def get_smtp_from_email() -> str:
    """Gibt die Absenderadresse fuer versendete E-Mails zurueck."""
    return os.getenv("SMTP_FROM_EMAIL", "no-reply@beetleatlas.local").strip()


def use_smtp_starttls() -> bool:
    """Gibt zurueck, ob STARTTLS fuer die SMTP-Verbindung genutzt wird."""
    return parse_bool_env("SMTP_USE_STARTTLS", True)


def use_smtp_ssl() -> bool:
    """Gibt zurueck, ob eine reine SSL-Verbindung fuer SMTP genutzt wird."""
    return parse_bool_env("SMTP_USE_SSL", False)


def get_redis_url() -> str:
    """Gibt die Redis-Verbindungs-URL fuer verteiltes Rate-Limiting zurueck."""
    return os.getenv("REDIS_URL", "").strip()
