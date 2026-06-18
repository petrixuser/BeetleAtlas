import threading
from collections import defaultdict, deque
from threading import Lock
from time import time

from fastapi import HTTPException, Request

from backend.config.settings import (
    get_auth_bootstrap_rate_limit,
    get_auth_login_rate_limit,
    get_auth_refresh_rate_limit,
    get_auth_register_rate_limit,
    get_redis_url,
)

try:
    import redis
except ImportError:  # pragma: no cover - optional dependency in some envs
    redis = None


_BUCKETS: dict[str, deque[float]] = defaultdict(deque)
_BUCKETS_LOCK = Lock()
_REDIS_CLIENT = None
_REDIS_CLIENT_LOCK = threading.Lock()
_REDIS_INITIALIZED = False


def _client_identity(request: Request) -> str:
    """Resolve best-effort client identity from headers or socket address."""
    forwarded_for = request.headers.get("x-forwarded-for")
    if forwarded_for:
        return forwarded_for.split(",", 1)[0].strip()

    if request.client and request.client.host:
        return request.client.host

    return "unknown"


def _get_redis_client():
    """Lazily create and cache a Redis client for distributed limits."""
    global _REDIS_CLIENT, _REDIS_INITIALIZED
    if _REDIS_INITIALIZED:
        return _REDIS_CLIENT

    with _REDIS_CLIENT_LOCK:
        if _REDIS_INITIALIZED:
            return _REDIS_CLIENT

        _REDIS_INITIALIZED = True
        redis_url = get_redis_url()
        if not redis_url or redis is None:
            _REDIS_CLIENT = None
            return None

        try:
            client = redis.Redis.from_url(
                redis_url,
                decode_responses=True,
                socket_connect_timeout=1,
                socket_timeout=1,
            )
            client.ping()
            _REDIS_CLIENT = client
        except Exception:
            _REDIS_CLIENT = None

    return _REDIS_CLIENT


def _redis_enforce_limit(bucket_key: str, max_requests: int, window_seconds: int) -> bool:
    """Try Redis fixed-window limiting. Return True if handled, else False."""
    client = _get_redis_client()
    if client is None:
        return False

    now = int(time())
    window_id = now // window_seconds
    redis_key = f"rl:{bucket_key}:{window_id}"

    try:
        count = int(client.incr(redis_key))
        if count == 1:
            client.expire(redis_key, window_seconds + 1)

        if count > max_requests:
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "rate_limited",
                    "message": "Too many requests. Please retry later.",
                },
            )
        return True
    except HTTPException:
        raise
    except Exception:
        return False


def _enforce_limit(bucket_key: str, max_requests: int, window_seconds: int) -> None:
    """Apply sliding-window limit on one in-memory bucket key."""
    if _redis_enforce_limit(bucket_key=bucket_key, max_requests=max_requests, window_seconds=window_seconds):
        return

    now = time()
    window_start = now - float(window_seconds)

    with _BUCKETS_LOCK:
        entries = _BUCKETS[bucket_key]
        while entries and entries[0] < window_start:
            entries.popleft()

        if len(entries) >= max_requests:
            raise HTTPException(
                status_code=429,
                detail={
                    "error": "rate_limited",
                    "message": "Too many requests. Please retry later.",
                },
            )

        entries.append(now)


def _apply_rate_limit(request: Request, action: str, max_requests: int, window_seconds: int) -> None:
    """Compose action+client bucket and enforce its request limit."""
    client = _client_identity(request)
    bucket_key = f"{action}:{client}"
    _enforce_limit(bucket_key=bucket_key, max_requests=max_requests, window_seconds=window_seconds)


def auth_register_rate_limit(request: Request) -> None:
    """Dependency for rate-limiting register requests."""
    max_requests, window_seconds = get_auth_register_rate_limit()
    _apply_rate_limit(request, "auth_register", max_requests, window_seconds)


def auth_login_rate_limit(request: Request) -> None:
    """Dependency for rate-limiting login requests."""
    max_requests, window_seconds = get_auth_login_rate_limit()
    _apply_rate_limit(request, "auth_login", max_requests, window_seconds)


def auth_refresh_rate_limit(request: Request) -> None:
    """Dependency for rate-limiting refresh requests."""
    max_requests, window_seconds = get_auth_refresh_rate_limit()
    _apply_rate_limit(request, "auth_refresh", max_requests, window_seconds)


def auth_bootstrap_rate_limit(request: Request) -> None:
    """Dependency for rate-limiting bootstrap-admin requests."""
    max_requests, window_seconds = get_auth_bootstrap_rate_limit()
    _apply_rate_limit(request, "auth_bootstrap", max_requests, window_seconds)
