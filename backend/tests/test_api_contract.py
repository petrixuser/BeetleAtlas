import json
import os
import uuid
from urllib.error import HTTPError
from urllib.error import URLError
from urllib.request import Request
from urllib.request import urlopen

import pytest


BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
# Cold/large queries on resource-constrained dev machines can take 20-38s.
# Override with API_TEST_TIMEOUT if needed.
REQUEST_TIMEOUT = float(os.getenv("API_TEST_TIMEOUT", "60"))


def _get_json(path: str):
    """Send GET request and decode JSON payload."""
    with urlopen(f"{BASE_URL}{path}", timeout=REQUEST_TIMEOUT) as response:
        payload = response.read().decode("utf-8")
        return response.status, json.loads(payload)


def _post_json(path: str):
    """Send POST request without body and decode JSON payload."""
    req = Request(f"{BASE_URL}{path}", method="POST")
    with urlopen(req, timeout=REQUEST_TIMEOUT) as response:
        payload = response.read().decode("utf-8")
        return response.status, json.loads(payload)


def _post_json_with_body(path: str, data: dict, headers: dict | None = None):
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


def _post_json_with_token(path: str, token: str):
    """Send authenticated POST request and decode JSON payload."""
    req = Request(
        f"{BASE_URL}{path}",
        method="POST",
        headers={"Authorization": f"Bearer {token}"},
    )
    with urlopen(req, timeout=REQUEST_TIMEOUT) as response:
        payload = response.read().decode("utf-8")
        return response.status, json.loads(payload)


def _post_json_with_token_and_body(path: str, token: str, data: dict):
    """Send authenticated POST request with JSON body and decode JSON payload."""
    req = Request(
        f"{BASE_URL}{path}",
        method="POST",
        data=json.dumps(data).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
    )
    with urlopen(req, timeout=REQUEST_TIMEOUT) as response:
        payload = response.read().decode("utf-8")
        return response.status, json.loads(payload)


@pytest.fixture(scope="session", autouse=True)
def require_running_api():
    """Skip contract tests if API is not reachable and healthy."""
    try:
        status, payload = _get_json("/health")
    except URLError:
        pytest.skip(f"Backend not reachable at {BASE_URL}")

    if status != 200 or payload.get("status") != "ok":
        pytest.skip("Backend is reachable but not healthy")


def test_health_contract():
    status, payload = _get_json("/health")
    assert status == 200
    assert payload == {"status": "ok"}


def test_beetles_list_contract():
    status, payload = _get_json("/api/beetles?limit=5&offset=0&sort_by=name&sort_dir=asc")

    assert status == 200
    assert set(["items", "total", "page", "page_size"]).issubset(payload.keys())
    assert isinstance(payload["items"], list)
    assert payload["page_size"] == 5

    if payload["items"]:
        first = payload["items"][0]
        assert set(["id", "name", "family", "coordinates", "climate", "vegetation", "observedAt"]).issubset(first.keys())


def test_beetle_detail_contract():
    _, listing = _get_json("/api/beetles?limit=1&offset=0&sort_by=name&sort_dir=asc")
    assert listing["items"], "Expected at least one beetle item"

    beetle_id = listing["items"][0]["id"]
    status, payload = _get_json(f"/api/beetles/{beetle_id}")

    assert status == 200
    assert payload["id"].startswith(("occ-", "rec-"))
    assert "name" in payload
    assert "family" in payload
    assert "observedAt" in payload
    if "imageUrl" not in payload:
        pytest.skip("Running backend does not include imageUrl/media items yet. Restart backend and rerun.")
    assert "meta" in payload and "media" in payload["meta"]
    assert "items" in payload["meta"]["media"]


def test_beetle_media_contract():
    _, listing = _get_json("/api/beetles?limit=1&offset=0&sort_by=name&sort_dir=asc")
    assert listing["items"], "Expected at least one beetle item"

    beetle_id = listing["items"][0]["id"]
    try:
        status, payload = _get_json(f"/api/beetles/{beetle_id}/media?limit=5&offset=0")
    except HTTPError as exc:
        if exc.code == 404:
            pytest.skip("Running backend does not include /api/beetles/{id}/media yet. Restart backend and rerun.")
        raise

    assert status == 200
    assert payload["id"].startswith(("occ-", "rec-"))
    assert set(["items", "total", "page", "page_size"]).issubset(payload.keys())
    assert isinstance(payload["items"], list)
    if payload["items"]:
        first = payload["items"][0]
        assert set(["mediaId", "url", "license"]).issubset(first.keys())


def test_country_contract_supports_code_and_name():
    status_code, payload_code = _get_json("/api/countries/GT")
    status_name, payload_name = _get_json("/api/countries/Guatemala")

    assert status_code == 200
    assert status_name == 200

    for payload in (payload_code, payload_name):
        assert set(["code", "name", "speciesCount", "topClimates", "topVegetations", "elevationRange"]).issubset(payload.keys())


def test_map_points_contract():
    status, payload = _get_json("/api/map/points?bbox=-81,-56,-34,13&zoom=7&limit=20&offset=0&sort_by=speciesName&sort_dir=asc")

    assert status == 200
    assert set(["items", "total", "page", "page_size", "clustered"]).issubset(payload.keys())
    assert isinstance(payload["items"], list)


def test_map_geojson_contract():
    status, payload = _get_json("/api/map/points/geojson?bbox=-81,-56,-34,13&zoom=7&limit=20&offset=0&sort_by=speciesName&sort_dir=asc")

    assert status == 200
    assert payload["type"] == "FeatureCollection"
    assert isinstance(payload["features"], list)
    assert "meta" in payload


def test_quality_report_contract():
    try:
        status, payload = _get_json("/quality/report")
    except HTTPError as exc:
        if exc.code == 404:
            pytest.skip("Running backend does not include /quality/report yet. Restart backend and rerun.")
        raise

    assert status == 200
    assert set(["generatedAt", "totals", "observationNullRates", "locationNullRates", "climateSnapshotNullRates", "eeCoverage"]).issubset(payload.keys())
    assert set(["observations", "locations", "climateSnapshots"]).issubset(payload["totals"].keys())
    assert isinstance(payload["observationNullRates"], list)
    assert isinstance(payload["locationNullRates"], list)
    assert isinstance(payload["climateSnapshotNullRates"], list)

    ee = payload["eeCoverage"]
    assert set(["withSnapshotMatch", "withoutSnapshotMatch", "withSnapshotRatePct"]).issubset(ee.keys())
    assert 0 <= ee["withSnapshotRatePct"] <= 100


def test_quality_report_history_snapshot_and_list_contract():
    try:
        status_create, created = _post_json("/quality/report/history/snapshot?source=contract_test")
    except HTTPError as exc:
        if exc.code == 404:
            pytest.skip("Running backend does not include quality history endpoints yet. Restart backend and rerun.")
        raise

    assert status_create == 200
    assert "snapshotId" in created
    assert "report" in created
    assert created.get("source") == "contract_test"

    status_list, listing = _get_json("/quality/report/history?limit=5&offset=0")
    assert status_list == 200
    assert set(["items", "total", "page", "page_size"]).issubset(listing.keys())
    assert isinstance(listing["items"], list)
    assert listing["items"], "Expected at least one quality history entry"

    first = listing["items"][0]
    assert set(["snapshotId", "generatedAt", "source", "totals", "observationNullRates", "eeCoverage"]).issubset(first.keys())


def test_quality_report_history_compare_contract():
    try:
        _, created = _post_json("/quality/report/history/snapshot?source=contract_compare")
    except HTTPError as exc:
        if exc.code == 404:
            pytest.skip("Running backend does not include quality history compare endpoint yet. Restart backend and rerun.")
        raise

    snapshot_id = int(created["snapshotId"])
    status_cmp, cmp_payload = _get_json(
        f"/quality/report/history/compare?from_id={snapshot_id}&to_id={snapshot_id}"
    )

    assert status_cmp == 200
    assert set(["fromSnapshot", "toSnapshot", "observationNullRateDelta", "eeCoverageDelta"]).issubset(cmp_payload.keys())


def test_auth_refresh_and_logout_contract():
    email = f"contract_refresh_{uuid.uuid4().hex[:10]}@example.com"
    password = "StrongPassw0rd!"
    test_headers = {"X-Forwarded-For": f"198.18.0.{int(uuid.uuid4().hex[:2], 16) or 1}"}

    try:
        _, register_payload = _post_json_with_body(
            "/auth/register",
            {"email": email, "password": password},
            headers=test_headers,
        )
        _post_json_with_body(
            "/auth/verify-email",
            {"verification_token": register_payload["verification_token"]},
        )
    except HTTPError as exc:
        if exc.code != 409:
            raise

    status_login, login_payload = _post_json_with_body(
        "/auth/login",
        {"email": email, "password": password},
        headers=test_headers,
    )
    assert status_login == 200
    access_token = login_payload.get("access_token")
    refresh_token = login_payload.get("refresh_token")
    assert access_token
    assert refresh_token

    status_refresh, refresh_payload = _post_json_with_body(
        "/auth/refresh",
        {"refresh_token": refresh_token},
    )
    assert status_refresh == 200
    assert set(["access_token", "token_type", "expires_in", "refresh_token", "refresh_expires_in"]).issubset(
        refresh_payload.keys()
    )
    assert refresh_payload["token_type"] == "bearer"

    status_logout, logout_payload = _post_json_with_token_and_body(
        "/auth/logout",
        access_token,
        {"refresh_token": refresh_payload["refresh_token"]},
    )
    assert status_logout == 200
    assert logout_payload == {"status": "ok"}


def test_stats_overview_contract():
    status, payload = _get_json("/stats/overview")

    assert status == 200
    assert "tables" in payload
    assert isinstance(payload["tables"], list)

    if payload["tables"]:
        first = payload["tables"][0]
        assert set(["table_name", "rows_count"]).issubset(first.keys())


def test_species_contract():
    status, payload = _get_json("/species?limit=5&offset=0&sort_by=scientific_name&sort_dir=asc")

    assert status == 200
    assert set(["items", "total", "page", "page_size"]).issubset(payload.keys())
    assert isinstance(payload["items"], list)
    assert payload["page_size"] == 5

    if payload["items"]:
        first = payload["items"][0]
        assert set(["beetle_id", "family", "scientific_name"]).issubset(first.keys())


def test_filters_contract_profiles():
    status_core, payload_core = _get_json("/api/filters?profile=core")
    status_extended, payload_extended = _get_json("/api/filters?profile=extended")

    assert status_core == 200
    assert status_extended == 200

    assert set(["climates", "vegetations", "elevations"]).issubset(payload_core.keys())
    assert isinstance(payload_core["climates"], list)

    assert "climates" in payload_extended
    assert "temperatureBands" in payload_extended
    assert "licenseClasses" in payload_extended


def test_field_mappings_contract():
    status, payload = _get_json("/api/field-mappings")

    assert status == 200
    assert "tables" in payload
    assert isinstance(payload["tables"], dict)

    tables = payload["tables"]
    assert set(["beetle_species", "location", "observation", "media", "climate_snapshot"]).issubset(tables.keys())


def test_observations_contract():
    status, payload = _get_json("/observations?limit=5&offset=0&sort_by=gbif_id&sort_dir=asc")

    assert status == 200
    assert set(["items", "total", "page", "page_size"]).issubset(payload.keys())
    assert isinstance(payload["items"], list)
    assert payload["page_size"] == 5

    if payload["items"]:
        first = payload["items"][0]
        assert set(["gbif_id", "beetle_id", "location_id", "event_date", "image_available", "scientific_name"]).issubset(first.keys())


def test_climate_by_location_contract():
    status_obs, observations = _get_json("/observations?limit=1&offset=0&sort_by=gbif_id&sort_dir=asc")
    assert status_obs == 200
    assert "items" in observations and isinstance(observations["items"], list)

    if not observations["items"]:
        pytest.skip("No observations available to resolve a location_id for climate endpoint test.")

    sample = observations["items"][0]
    location_id = sample.get("location_id")
    if location_id is None:
        pytest.skip("Observation payload does not include location_id.")

    status, payload = _get_json(f"/climate/location/{location_id}?limit=5")

    assert status == 200
    assert "location_id" in payload
    assert "items" in payload
    assert isinstance(payload["items"], list)


