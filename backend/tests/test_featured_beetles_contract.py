"""Regressionstest fuer die Featured-Kaefer.

Sichert genau den Bug ab, bei dem die statische Liste frontend/data/featured-beetles.js
auf rec-IDs verwies, die es im Backend (nach einem DB-Neuaufbau) nicht gab:
  * jede in featured-beetles.js hinterlegte rec-ID muss im Backend aufloesbar sein
  * und der Datensatz muss die Steckbrief-Stats (Temperatur/Klima/Vegetation/Hoehe) tragen.
So faellt ein erneutes "Driften" der IDs sofort auf.
"""

import json
import os
import re
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

import pytest

BASE_URL = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")
REQUEST_TIMEOUT = float(os.getenv("API_TEST_TIMEOUT", "60"))

# Repo-Root: backend/tests/ -> zwei Ebenen hoch.
_REPO_ROOT = Path(__file__).resolve().parents[2]
_FEATURED_FILE = _REPO_ROOT / "frontend" / "data" / "featured-beetles.js"


def _load_featured_ids() -> list[str]:
    """Liest die rec-IDs aus der statischen featured-beetles.js (JSON-Array)."""
    if not _FEATURED_FILE.exists():
        pytest.skip(f"featured-beetles.js nicht gefunden unter {_FEATURED_FILE}")
    text = _FEATURED_FILE.read_text(encoding="utf-8")
    start = text.index("[")
    end = text.rindex("]") + 1
    entries = json.loads(text[start:end])
    return [str(e["id"]) for e in entries if str(e.get("id", "")).startswith("rec-")]


def _load_featured_names() -> list[str]:
    """Liest die scientific_name-Werte (Feld 'name') aus der statischen Liste."""
    if not _FEATURED_FILE.exists():
        pytest.skip(f"featured-beetles.js nicht gefunden unter {_FEATURED_FILE}")
    text = _FEATURED_FILE.read_text(encoding="utf-8")
    start = text.index("[")
    end = text.rindex("]") + 1
    entries = json.loads(text[start:end])
    return [str(e["name"]) for e in entries if e.get("name")]


def _get_json(path: str):
    """GET-Request; liefert (status, payload). 404 wird als (404, {...}) zurueckgegeben."""
    req = Request(f"{BASE_URL}{path}", method="GET", headers={"Accept": "application/json"})
    try:
        with urlopen(req, timeout=REQUEST_TIMEOUT) as response:
            return response.status, json.loads(response.read().decode("utf-8"))
    except HTTPError as exc:
        try:
            payload = json.loads(exc.read().decode("utf-8"))
        except Exception:
            payload = {}
        return exc.code, payload
    except URLError as exc:
        pytest.skip(f"Backend nicht erreichbar unter {BASE_URL}: {exc}")


def test_featured_file_has_entries():
    """Die statische Featured-Liste ist nicht leer."""
    ids = _load_featured_ids()
    assert len(ids) >= 1


def test_every_featured_id_resolves_with_stats():
    """Jede Featured-rec-ID ist im Backend vorhanden und traegt Steckbrief-Stats."""
    ids = _load_featured_ids()
    missing = []
    without_stats = []

    for beetle_id in ids:
        status, payload = _get_json(f"/api/beetles/{beetle_id}")
        if status == 404:
            missing.append(beetle_id)
            continue
        assert status == 200, f"{beetle_id}: unerwarteter Status {status}"
        assert payload.get("name"), f"{beetle_id}: kein Name"
        has_stats = all(
            payload.get(field) is not None
            for field in ("temperature", "climate", "vegetation", "elevation")
        )
        if not has_stats:
            without_stats.append(beetle_id)

    assert not missing, f"Featured-IDs ohne Backend-Datensatz (404): {missing}"
    assert not without_stats, f"Featured-IDs ohne vollstaendige Stats: {without_stats}"


def test_featured_endpoint_covers_static_names():
    """Der /api/beetles/featured-Endpoint liefert fuer jeden statischen Namen eine
    echte rec-ID, damit der Frontend-Abgleich (featured-sync.js) jede Karte pinnen kann."""
    status, payload = _get_json("/api/beetles/featured")
    assert status == 200, f"unerwarteter Status {status}"
    items = payload.get("items") or []
    assert len(items) >= 1
    for item in items:
        assert str(item.get("id", "")).startswith("rec-"), f"ungueltige ID: {item}"
        assert item.get("name"), f"Eintrag ohne Name: {item}"

    endpoint_names = {item["name"] for item in items}
    static_names = set(_load_featured_names())
    fehlend = static_names - endpoint_names
    assert not fehlend, f"Namen aus featured-beetles.js ohne Backend-Eintrag: {fehlend}"
