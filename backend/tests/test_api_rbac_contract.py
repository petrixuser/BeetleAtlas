import json
import os
import uuid
from urllib.error import HTTPError
from urllib.error import URLError
from urllib.request import Request
from urllib.request import urlopen

import pytest


BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
REQUEST_TIMEOUT = float(os.getenv("API_TEST_TIMEOUT", "60"))
ADMIN_EMAIL = os.getenv("API_ADMIN_EMAIL", "admin.contract@example.com")
ADMIN_PASSWORD = os.getenv("API_ADMIN_PASSWORD", "AdminContract123!")
BOOTSTRAP_TOKEN = os.getenv("API_BOOTSTRAP_TOKEN", "dev-bootstrap-token")
RESEARCHER_SIGNUP_CODE = os.getenv("API_RESEARCHER_SIGNUP_CODE", "dev-researcher-code")


def _request_json(
    path: str,
    method: str = "GET",
    data: dict | None = None,
    token: str | None = None,
    extra_headers: dict | None = None,
):
    body = None
    headers = {}
    if data is not None:
        body = json.dumps(data).encode("utf-8")
        headers["Content-Type"] = "application/json"

    if token:
        headers["Authorization"] = f"Bearer {token}"

    if extra_headers:
        headers.update(extra_headers)

    req = Request(f"{BASE_URL}{path}", data=body, headers=headers, method=method)
    with urlopen(req, timeout=REQUEST_TIMEOUT) as response:
        payload = response.read().decode("utf-8")
        return response.status, json.loads(payload)


@pytest.fixture(scope="session", autouse=True)
def require_running_api():
    try:
        status, payload = _request_json("/health")
    except URLError:
        pytest.skip(f"Backend not reachable at {BASE_URL}")

    if status != 200 or payload.get("status") != "ok":
        pytest.skip("Backend is reachable but not healthy")


def _register_and_login_researcher() -> str:
    email = f"contract_researcher_{uuid.uuid4().hex[:8]}@example.com"
    password = "StrongPassw0rd!"
    test_headers = {"X-Forwarded-For": f"198.51.100.{int(uuid.uuid4().hex[:2], 16) or 1}"}

    status_reg, register_payload = _request_json(
        "/auth/register",
        method="POST",
        data={
            "email": email,
            "password": password,
            "role": "researcher",
            "researcher_signup_code": RESEARCHER_SIGNUP_CODE,
        },
        extra_headers=test_headers,
    )
    assert status_reg == 200

    status_verify, _ = _request_json(
        "/auth/verify-email",
        method="POST",
        data={"verification_token": register_payload["verification_token"]},
        extra_headers=test_headers,
    )
    assert status_verify == 200

    status_login, login_payload = _request_json(
        "/auth/login",
        method="POST",
        data={"email": email, "password": password},
        extra_headers=test_headers,
    )
    assert status_login == 200
    assert "access_token" in login_payload
    return login_payload["access_token"]


def _register_and_login_viewer() -> str:
    email = f"contract_viewer_{uuid.uuid4().hex[:8]}@example.com"
    password = "StrongPassw0rd!"
    test_headers = {"X-Forwarded-For": f"203.0.113.{int(uuid.uuid4().hex[:2], 16) or 1}"}

    status_reg, register_payload = _request_json(
        "/auth/register",
        method="POST",
        data={"email": email, "password": password, "role": "viewer"},
        extra_headers=test_headers,
    )
    assert status_reg == 200

    status_verify, _ = _request_json(
        "/auth/verify-email",
        method="POST",
        data={"verification_token": register_payload["verification_token"]},
        extra_headers=test_headers,
    )
    assert status_verify == 200

    status_login, login_payload = _request_json(
        "/auth/login",
        method="POST",
        data={"email": email, "password": password},
        extra_headers=test_headers,
    )
    assert status_login == 200
    assert "access_token" in login_payload
    return login_payload["access_token"]


def _login_admin_or_skip() -> str:
    try:
        _request_json(
            "/auth/bootstrap-admin",
            method="POST",
            data={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
            extra_headers={"X-Bootstrap-Token": BOOTSTRAP_TOKEN},
        )
    except HTTPError as exc:
        if exc.code in (403, 404, 503):
            pytest.skip(
                "Admin bootstrap not available. Enable ALLOW_ADMIN_BOOTSTRAP and set matching bootstrap token."
            )
        raise

    status_login, payload = _request_json(
        "/auth/login",
        method="POST",
        data={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD},
    )
    assert status_login == 200
    assert "access_token" in payload
    return payload["access_token"]


def _create_record(token: str) -> int:
    status, payload = _request_json(
        "/api/beetles",
        method="POST",
        token=token,
        data={
            "scientific_name": "Testus contractus",
            "family": "Contractidae",
            "genus": "Testus",
            "country": "GT",
            "location": "Guatemala City",
            "notes": "created by contract test",
        },
    )
    assert status == 200
    assert "id" in payload
    return int(payload["id"])


def test_researcher_can_create_beetle_record_contract():
    researcher_token = _register_and_login_researcher()
    record_id = _create_record(researcher_token)
    assert record_id > 0


def test_researcher_created_record_has_public_rec_detail_contract():
    researcher_token = _register_and_login_researcher()
    record_id = _create_record(researcher_token)

    status, payload = _request_json(f"/api/beetles/rec-{record_id}")
    assert status == 200
    assert payload["id"] == f"rec-{record_id}"
    assert payload["name"] == "Testus contractus"


def test_researcher_created_record_has_rec_media_contract():
    researcher_token = _register_and_login_researcher()

    status_create, created = _request_json(
        "/api/beetles",
        method="POST",
        token=researcher_token,
        data={
            "scientific_name": "Rec media contractus",
            "family": "Contractidae",
            "image_url": "https://example.org/beetle.jpg",
            "media_license": "CC-BY-4.0",
            "media_creator": "Contract Tester",
            "media_publisher": "QA",
            "media_rights_holder": "QA Team",
            "media_references": "https://example.org/reference",
        },
    )
    assert status_create == 200
    record_id = int(created["id"])

    status_media, media_payload = _request_json(f"/api/beetles/rec-{record_id}/media?limit=5&offset=0")
    assert status_media == 200
    assert media_payload["id"] == f"rec-{record_id}"
    assert media_payload["total"] == 1
    assert len(media_payload["items"]) == 1

    first = media_payload["items"][0]
    assert first["mediaId"] == f"manual-{record_id}"
    assert first["url"] == "https://example.org/beetle.jpg"
    assert first["license"] == "CC-BY-4.0"
    assert first["creator"] == "Contract Tester"
    assert first["publisher"] == "QA"
    assert first["rightsHolder"] == "QA Team"
    assert first["references"] == "https://example.org/reference"


def test_researcher_cannot_set_gbif_id_on_create_contract():
    researcher_token = _register_and_login_researcher()

    try:
        _request_json(
            "/api/beetles",
            method="POST",
            token=researcher_token,
            data={
                "gbif_id": 987654321,
                "scientific_name": "GBIF blocked create",
                "family": "Contractidae",
            },
        )
        pytest.fail("Expected 403 when researcher sets gbif_id on create")
    except HTTPError as exc:
        assert exc.code == 403
        payload = json.loads(exc.read().decode("utf-8"))
        assert payload == {
            "error": "forbidden",
            "message": "Researchers are not allowed to set gbif_id.",
        }


def test_researcher_can_update_own_beetle_record_contract():
    researcher_token = _register_and_login_researcher()
    record_id = _create_record(researcher_token)

    status_patch, patched = _request_json(
        f"/api/beetles/{record_id}",
        method="PATCH",
        token=researcher_token,
        data={"notes": "patched by creator"},
    )
    assert status_patch == 200
    assert patched["id"] == record_id
    assert patched["notes"] == "patched by creator"


def test_researcher_cannot_set_gbif_id_on_update_contract():
    researcher_token = _register_and_login_researcher()
    record_id = _create_record(researcher_token)

    try:
        _request_json(
            f"/api/beetles/{record_id}",
            method="PATCH",
            token=researcher_token,
            data={"gbif_id": 123456789},
        )
        pytest.fail("Expected 403 when researcher sets gbif_id on update")
    except HTTPError as exc:
        assert exc.code == 403
        payload = json.loads(exc.read().decode("utf-8"))
        assert payload == {
            "error": "forbidden",
            "message": "Researchers are not allowed to set gbif_id.",
        }


def test_researcher_cannot_update_foreign_beetle_record_contract():
    researcher_one = _register_and_login_researcher()
    researcher_two = _register_and_login_researcher()
    record_id = _create_record(researcher_one)

    try:
        _request_json(
            f"/api/beetles/{record_id}",
            method="PATCH",
            token=researcher_two,
            data={"notes": "unauthorized patch"},
        )
        pytest.fail("Expected 403 when researcher updates foreign record")
    except HTTPError as exc:
        assert exc.code == 403
        payload = json.loads(exc.read().decode("utf-8"))
        assert payload == {"error": "forbidden", "message": "Insufficient permissions."}


def test_researcher_cannot_delete_beetle_record_contract():
    researcher_token = _register_and_login_researcher()
    record_id = _create_record(researcher_token)

    try:
        _request_json(f"/api/beetles/{record_id}", method="DELETE", token=researcher_token)
        pytest.fail("Expected 403 for researcher delete attempt")
    except HTTPError as exc:
        assert exc.code == 403
        payload = json.loads(exc.read().decode("utf-8"))
        assert payload == {"error": "forbidden", "message": "Insufficient permissions."}


def test_admin_can_update_and_delete_beetle_record_contract():
    admin_token = _login_admin_or_skip()
    record_id = _create_record(admin_token)

    status_patch, patched = _request_json(
        f"/api/beetles/{record_id}",
        method="PATCH",
        token=admin_token,
        data={"notes": "patched by admin contract test"},
    )
    assert status_patch == 200
    assert patched["id"] == record_id
    assert patched["notes"] == "patched by admin contract test"

    status_delete, deleted = _request_json(
        f"/api/beetles/{record_id}",
        method="DELETE",
        token=admin_token,
    )
    assert status_delete == 200
    assert deleted == {"status": "deleted", "id": record_id}


def test_write_endpoints_require_auth_contract():
    try:
        _request_json(
            "/api/beetles",
            method="POST",
            data={"scientific_name": "NoAuth test", "family": "NoAuthidae"},
        )
        pytest.fail("Expected 401 without bearer token")
    except HTTPError as exc:
        assert exc.code == 401
        payload = json.loads(exc.read().decode("utf-8"))
        assert payload == {"error": "unauthorized", "message": "Missing or invalid bearer token."}


def test_viewer_cannot_create_beetle_record_contract():
    viewer_token = _register_and_login_viewer()

    try:
        _request_json(
            "/api/beetles",
            method="POST",
            token=viewer_token,
            data={
                "scientific_name": "Viewer blocked create",
                "family": "Vieweridae",
            },
        )
        pytest.fail("Expected 403 when viewer creates a beetle record")
    except HTTPError as exc:
        assert exc.code == 403
        payload = json.loads(exc.read().decode("utf-8"))
        assert payload == {"error": "forbidden", "message": "Insufficient permissions."}


def test_viewer_cannot_update_beetle_record_contract():
    researcher_token = _register_and_login_researcher()
    viewer_token = _register_and_login_viewer()
    record_id = _create_record(researcher_token)

    try:
        _request_json(
            f"/api/beetles/{record_id}",
            method="PATCH",
            token=viewer_token,
            data={"notes": "viewer patch attempt"},
        )
        pytest.fail("Expected 403 when viewer updates a beetle record")
    except HTTPError as exc:
        assert exc.code == 403
        payload = json.loads(exc.read().decode("utf-8"))
        assert payload == {"error": "forbidden", "message": "Insufficient permissions."}
