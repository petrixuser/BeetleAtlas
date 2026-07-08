"""Zentrale Fehler-Codes fuer einheitliche API-Fehlerantworten."""


class _Common:
    NOT_FOUND = "not_found"
    FORBIDDEN = "forbidden"


class _Core:
    INVALID_PAGINATION = "invalid_pagination"
    INVALID_SORT = "invalid_sort"
    INVALID_BBOX = "invalid_bbox"


class _Auth:
    INVALID_EMAIL = "invalid_email"
    EMAIL_EXISTS = "email_exists"
    RESEARCHER_SIGNUP_UNAVAILABLE = "researcher_signup_unavailable"
    REGISTRATION_FAILED = "registration_failed"
    INVALID_CREDENTIALS = "invalid_credentials"
    ACCOUNT_INACTIVE = "account_inactive"
    INVALID_REFRESH_TOKEN = "invalid_refresh_token"
    BOOTSTRAP_UNAVAILABLE = "bootstrap_unavailable"
    ADMIN_EXISTS = "admin_exists"
    BOOTSTRAP_FAILED = "bootstrap_failed"
    EMAIL_NOT_VERIFIED = "email_not_verified"
    INVALID_VERIFICATION_TOKEN = "invalid_verification_token"
    EMAIL_DELIVERY_FAILED = "email_delivery_failed"


class _Beetle:
    INVALID_ID = "invalid_id"
    INVALID_COUNTRY_CODE = "invalid_country_code"


class _BeetleWrite:
    GBIF_ID_EXISTS = "gbif_id_exists"
    CREATE_FAILED = "create_failed"


class ERR:
    COMMON = _Common
    CORE = _Core
    AUTH = _Auth
    BEETLE = _Beetle
    BEETLE_WRITE = _BeetleWrite


def _validate_unique_codes() -> None:
    """Prueft, dass alle definierten Fehlercodes ueber alle Gruppen hinweg eindeutig sind."""
    groups = {
        "COMMON": ERR.COMMON,
        "CORE": ERR.CORE,
        "AUTH": ERR.AUTH,
        "BEETLE": ERR.BEETLE,
        "BEETLE_WRITE": ERR.BEETLE_WRITE,
    }

    seen = {}
    duplicates = []
    for group_name, group in groups.items():
        for key, value in vars(group).items():
            if key.startswith("_") or not isinstance(value, str):
                continue
            previous = seen.get(value)
            if previous is not None:
                duplicates.append((value, previous, f"{group_name}.{key}"))
            else:
                seen[value] = f"{group_name}.{key}"

    if duplicates:
        details = ", ".join(
            f"{code} ({first} / {second})" for code, first, second in duplicates
        )
        raise RuntimeError(f"Duplicate error codes detected: {details}")


_validate_unique_codes()
