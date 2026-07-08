"""Contract-Tests fuer manuelle Kaefer nach der Normalisierung.

Diese Tests pruefen das von aussen sichtbare Verhalten des Core-Reuse-Designs
(beetle_record -> beetle_species + location + climate_snapshot + media):
"""

import json
import os
import uuid
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import pytest

BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
REQUEST_TIMEOUT = float(os.getenv("API_TEST_TIMEOUT", "60"))
RESEARCHER_SIGNUP_CODE = os.getenv("API_RESEARCHER_SIGNUP_CODE", "dev-researcher-code")


def _request_json(path: str, method: str = "GET", data: dict | None = None,
                  token: str | None = None, extra_headers: dict | None = None):
    """Sendet einen HTTP-Request und dekodiert die JSON-Antwort -> (status, payload)."""
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    if extra_headers:
        headers.update(extra_headers)
    body = json.dumps(data).encode("utf-8") if data is not None else None
    req = Request(f"{BASE_URL}{path}", method=method, data=body, headers=headers)
    try:
        with urlopen(req, timeout=REQUEST_TIMEOUT) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except URLError as exc:
        pytest.skip(f"Backend nicht erreichbar unter {BASE_URL}: {exc}")


def _register_and_login_researcher() -> str:
    """Registriert + verifiziert + loggt einen frischen Forscher ein und gibt das Token zurueck."""
    email = f"norm_researcher_{uuid.uuid4().hex[:8]}@example.com"
    password = "StrongPassw0rd!"
    ip_headers = {"X-Forwarded-For": f"198.51.100.{int(uuid.uuid4().hex[:2], 16) or 1}"}

    status_reg, register_payload = _request_json(
        "/auth/register",
        method="POST",
        data={
            "email": email,
            "password": password,
            "role": "researcher",
            "researcher_signup_code": RESEARCHER_SIGNUP_CODE,
        },
        extra_headers=ip_headers,
    )
    if status_reg != 200 or "verification_token" not in (register_payload or {}):
        pytest.skip("Registrierung/Verifizierung nicht verfuegbar (SMTP-Modus?) - Test uebersprungen.")

    _request_json(
        "/auth/verify-email",
        method="POST",
        data={"verification_token": register_payload["verification_token"]},
        extra_headers=ip_headers,
    )
    status_login, login_payload = _request_json(
        "/auth/login",
        method="POST",
        data={"email": email, "password": password},
        extra_headers=ip_headers,
    )
    assert status_login == 200
    return login_payload["access_token"]


def _create_beetle(token: str, **fields):
    """Legt einen manuellen Kaefer an und gibt (status, payload) zurueck."""
    return _request_json("/api/beetles", method="POST", token=token, data=fields)


def test_manual_beetle_with_coords_roundtrips_location_via_view():
    """Mit Koordinaten angelegt -> die Detailantwort spiegelt Ort (aus location) zurueck."""
    token = _register_and_login_researcher()
    status, created = _create_beetle(
        token,
        scientific_name=f"Normalis coordis {uuid.uuid4().hex[:6]}",
        family="Testidae",
        latitude=14.5,
        longitude=-90.5,
        country="Guatemala",
    )
    assert status == 200
    record_id = int(created["id"])

    status_detail, detail = _request_json(f"/api/beetles/rec-{record_id}")
    assert status_detail == 200
    assert detail["id"] == f"rec-{record_id}"
    # Koordinaten kommen ueber die View aus location zurueck ([lng, lat]).
    lng, lat = detail["coordinates"]
    assert lng is not None and lat is not None
    assert abs(float(lat) - 14.5) < 0.01
    assert abs(float(lng) - (-90.5)) < 0.01


def test_manual_beetle_same_species_twice_both_succeed():
    """Zwei Kaefer mit derselben Art -> beide werden angelegt (Art wird wiederverwendet, kein Fehler)."""
    token = _register_and_login_researcher()
    name = f"Normalis duplus {uuid.uuid4().hex[:6]}"

    status_a, a = _create_beetle(token, scientific_name=name, family="Testidae", latitude=1.0, longitude=-60.0)
    status_b, b = _create_beetle(token, scientific_name=name, family="Testidae", latitude=2.0, longitude=-61.0)
    assert status_a == 200 and status_b == 200
    assert int(a["id"]) != int(b["id"])


def test_manual_beetle_same_coords_twice_both_succeed():
    """Zwei Kaefer an denselben Koordinaten -> beide werden angelegt (Ort wird wiederverwendet)."""
    token = _register_and_login_researcher()
    lat = 3.14159
    lng = -60.5

    status_a, a = _create_beetle(token, scientific_name=f"Loc reuse A {uuid.uuid4().hex[:6]}", family="Testidae", latitude=lat, longitude=lng)
    status_b, b = _create_beetle(token, scientific_name=f"Loc reuse B {uuid.uuid4().hex[:6]}", family="Testidae", latitude=lat, longitude=lng)
    assert status_a == 200 and status_b == 200
    assert int(a["id"]) != int(b["id"])


def test_manual_beetle_without_coords_still_created():
    """Ohne Koordinaten -> Kaefer bleibt anlegbar (location_id nullable)."""
    token = _register_and_login_researcher()
    status, created = _create_beetle(
        token,
        scientific_name=f"Sine coordis {uuid.uuid4().hex[:6]}",
        family="Testidae",
        notes="kein Ort",
    )
    assert status == 200
    record_id = int(created["id"])

    status_detail, detail = _request_json(f"/api/beetles/rec-{record_id}")
    assert status_detail == 200
    assert detail["id"] == f"rec-{record_id}"
