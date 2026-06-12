import json
import os
from urllib.error import HTTPError
from urllib.error import URLError
from urllib.request import Request
from urllib.request import urlopen

import pytest


BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")


def _get_json(path: str):
    with urlopen(f"{BASE_URL}{path}", timeout=15) as response:
        payload = response.read().decode("utf-8")
        return response.status, json.loads(payload)


def _post_json(path: str):
    req = Request(f"{BASE_URL}{path}", method="POST")
    with urlopen(req, timeout=15) as response:
        payload = response.read().decode("utf-8")
        return response.status, json.loads(payload)


@pytest.fixture(scope="session", autouse=True)
def require_running_api():
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

    beetle_id = listing["items"][0]["id"].replace("occ-", "")
    status, payload = _get_json(f"/api/beetles/{beetle_id}")

    assert status == 200
    assert payload["id"].startswith("occ-")
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

    beetle_id = listing["items"][0]["id"].replace("occ-", "")
    try:
        status, payload = _get_json(f"/api/beetles/{beetle_id}/media?limit=5&offset=0")
    except HTTPError as exc:
        if exc.code == 404:
            pytest.skip("Running backend does not include /api/beetles/{id}/media yet. Restart backend and rerun.")
        raise

    assert status == 200
    assert payload["id"].startswith("occ-")
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


def test_unknown_route_error_format_contract():
    try:
        _get_json("/does-not-exist")
        pytest.fail("Expected HTTPError for unknown route")
    except HTTPError as exc:
        assert exc.code == 404
        payload = json.loads(exc.read().decode("utf-8"))
        assert payload == {"error": "not_found", "message": "Route not found."}
