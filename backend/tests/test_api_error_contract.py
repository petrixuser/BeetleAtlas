import json
import os
import uuid
from urllib.error import HTTPError
from urllib.error import URLError
from urllib.request import urlopen
from urllib.request import Request

import pytest


BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
REQUEST_TIMEOUT = float(os.getenv("API_TEST_TIMEOUT", "60"))


def _get_json(path: str):
    """Send GET request and decode JSON payload."""
    with urlopen(f"{BASE_URL}{path}", timeout=REQUEST_TIMEOUT) as response:
        payload = response.read().decode("utf-8")
        return response.status, json.loads(payload)


def _post_json(path: str, data: dict, headers: dict | None = None):
    """Send POST request with JSON body and decode JSON payload."""
    request_headers = {"Content-Type": "application/json"}
    if headers:
        request_headers.update(headers)

    req = Request(
        f"{BASE_URL}{path}",
        method="POST",
        data=json.dumps(data).encode("utf-8"),
        headers=request_headers,
    )
    with urlopen(req, timeout=REQUEST_TIMEOUT) as response:
        payload = response.read().decode("utf-8")
        return response.status, json.loads(payload)


@pytest.fixture(scope="session", autouse=True)
def require_running_api():
    """Skip error-contract tests if API is not reachable and healthy."""
    try:
        status, payload = _get_json("/health")
    except URLError:
        pytest.skip(f"Backend not reachable at {BASE_URL}")

    if status != 200 or payload.get("status") != "ok":
        pytest.skip("Backend is reachable but not healthy")


def test_validation_error_contract_for_invalid_beetles_sort_by():
    try:
        _get_json("/api/beetles?limit=5&offset=0&sort_by=invalid_sort&sort_dir=asc")
        pytest.fail("Expected HTTPError for invalid sort_by")
    except HTTPError as exc:
        assert exc.code == 422
        payload = json.loads(exc.read().decode("utf-8"))
        assert payload == {"error": "validation_error", "message": "Ungueltige Anfrageparameter."}


def test_validation_error_contract_for_map_points_missing_bbox():
    try:
        _get_json("/api/map/points?zoom=7&limit=20&offset=0&sort_by=speciesName&sort_dir=asc")
        pytest.fail("Expected HTTPError when bbox is missing")
    except HTTPError as exc:
        assert exc.code == 422
        payload = json.loads(exc.read().decode("utf-8"))
        assert payload == {"error": "validation_error", "message": "Ungueltige Anfrageparameter."}


def test_validation_error_contract_for_map_points_invalid_zoom():
    try:
        _get_json("/api/map/points?bbox=-81,-56,-34,13&zoom=99&limit=20&offset=0&sort_by=speciesName&sort_dir=asc")
        pytest.fail("Expected HTTPError when zoom is out of allowed range")
    except HTTPError as exc:
        assert exc.code == 422
        payload = json.loads(exc.read().decode("utf-8"))
        assert payload == {"error": "validation_error", "message": "Ungueltige Anfrageparameter."}


def test_unknown_route_error_format_contract():
    try:
        _get_json("/does-not-exist")
        pytest.fail("Expected HTTPError for unknown route")
    except HTTPError as exc:
        assert exc.code == 404
        payload = json.loads(exc.read().decode("utf-8"))
        assert payload == {"error": "not_found", "message": "Route nicht gefunden."}


def test_login_rate_limit_contract():
    """Repeated failed logins should eventually return the 429 rate-limit envelope."""
    got_429 = False

    test_headers = {"X-Forwarded-For": "198.51.100.77"}

    for _ in range(40):
        try:
            _post_json(
                "/auth/login",
                {"email": "rate-limit-test@example.com", "password": "WrongPassword123!"},
                headers=test_headers,
            )
        except HTTPError as exc:
            payload = json.loads(exc.read().decode("utf-8"))
            if exc.code == 429:
                assert payload == {
                    "error": "rate_limited",
                    "message": "Zu viele Anfragen. Bitte spaeter erneut versuchen.",
                }
                got_429 = True
                break
            if exc.code != 401:
                raise

    assert got_429, "Expected login endpoint to enforce rate limiting with HTTP 429."


def test_register_defaults_to_viewer_role_contract():
    email = f"viewer_default_{uuid.uuid4().hex[:10]}@example.com"
    test_headers = {"X-Forwarded-For": f"198.51.100.{int(uuid.uuid4().hex[:2], 16) or 1}"}
    status, payload = _post_json(
        "/auth/register",
        {"email": email, "password": "ViewerDefault123!"},
        headers=test_headers,
    )

    assert status == 200
    assert payload["status"] == "pending_verification"
    assert payload["email"] == email
    assert isinstance(payload.get("verification_token"), str)
    assert int(payload.get("verification_expires_in") or 0) > 0


def test_researcher_register_requires_valid_signup_code_contract():
    email = f"researcher_code_{uuid.uuid4().hex[:10]}@example.com"
    test_headers = {"X-Forwarded-For": f"203.0.113.{int(uuid.uuid4().hex[:2], 16) or 1}"}

    try:
        _post_json(
            "/auth/register",
            {
                "email": email,
                "password": "ResearcherCode123!",
                "role": "researcher",
                "researcher_signup_code": "wrong-code",
            },
            headers=test_headers,
        )
        pytest.fail("Expected researcher registration to fail with invalid signup code")
    except HTTPError as exc:
        assert exc.code in (403, 503)
        payload = json.loads(exc.read().decode("utf-8"))
        assert payload["error"] in {"forbidden", "researcher_signup_unavailable"}