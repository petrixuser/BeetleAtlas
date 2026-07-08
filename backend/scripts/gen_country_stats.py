#!/usr/bin/env python3
"""Generiert den vorberechneten Laender-Snapshot fuer das Frontend.

Hintergrund: Der Endpunkt /api/countries/{code} ist langsam (correlated subquery
ueber climate_snapshot, ~2-4 s/Land). Statt ihn bei jedem Klick live aufzurufen,
berechnen wir die Laenderdaten EINMALIG vor und backen sie als statische Datei
`frontend/data/country-stats.js`. Im Browser ist der Klick dann instant und es
entsteht keine laufende DB-Last.

Aufruf (Backend muss mit der erweiterten /api/countries-Antwort deployt sein):

    python3 backend/scripts/gen_country_stats.py
    # optional anderes Backend:
    python3 backend/scripts/gen_country_stats.py --base https://api-kafer.server-work.de

Das Skript braucht KEINE externen Pakete (nur die Standardbibliothek).

Namens-Matching: Die DB speichert Laender gemischt — grosse Laender als Name
("Brazil", "Mexico"), kleinere als ISO-Code ("GF", "MQ", "BZ", "JM", ...). Pro
Land probieren wir darum mehrere Kandidaten (Anzeigename + ISO2) und nehmen den
ersten, der Daten liefert. So bleibt das Matching an EINER Stelle geloest.
"""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

DEFAULT_BASE = "https://api-kafer.server-work.de"

# Klickbare Laender = die Labels, die das Frontend auf der Karte fuehrt
# (frontend/app.js -> labelPositions). Key = exakter GeoJSON-/Label-Name, den
# openCountrySidebar(name) spaeter nachschlaegt. Wert = ISO2-Code als zweiter
# Lookup-Kandidat (fuer Laender, die in der DB als Code gespeichert sind).
COUNTRIES = {
    "Argentina": "AR",
    "Belize": "BZ",
    "Bolivia": "BO",
    "Brazil": "BR",
    "Chile": "CL",
    "Colombia": "CO",
    "Costa Rica": "CR",
    "Cuba": "CU",
    "Dominican Republic": "DO",
    "Ecuador": "EC",
    "El Salvador": "SV",
    "French Guiana": "GF",
    "Guatemala": "GT",
    "Guyana": "GY",
    "Haiti": "HT",
    "Honduras": "HN",
    "Jamaica": "JM",
    "Mexico": "MX",
    "Nicaragua": "NI",
    "Panama": "PA",
    "Paraguay": "PY",
    "Peru": "PE",
    "Puerto Rico": "PR",
    "Suriname": "SR",
    "Uruguay": "UY",
    "Venezuela": "VE",
}

OUTPUT = Path(__file__).resolve().parents[2] / "frontend" / "data" / "country-stats.js"


def fetch_country(base: str, lookup: str):
    """Fragt /api/countries/{lookup} ab und liefert das JSON als dict oder None."""
    url = f"{base}/api/countries/{urllib.parse.quote(lookup)}"
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/126.0 Safari/537.36"
            ),
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            if resp.status != 200:
                return None
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        if exc.code == 404:
            return None
        raise
    except urllib.error.URLError:
        return None


def resolve_country(base: str, display_name: str, iso2: str):
    """Versucht, Laenderdaten anhand des Anzeigenamens oder ISO2-Codes zu erhalten."""
    for candidate in (display_name, iso2):
        data = fetch_country(base, candidate)
        if data and (data.get("speciesCount") or 0) > 0:
            return data, candidate
    return None, None


def main() -> int:
    """Ruft pro klickbarem Land die API ab und schreibt frontend/data/country-stats.js."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base", default=DEFAULT_BASE, help="Backend-Basis-URL")
    args = parser.parse_args()
    base = args.base.rstrip("/")

    stats = {}
    missing = []
    for display_name, iso2 in COUNTRIES.items():
        data, used = resolve_country(base, display_name, iso2)
        if data is None:
            missing.append(display_name)
            print(f"  -  {display_name:<20} keine Daten (probiert: {display_name!r}, {iso2!r})")
            continue
        # Der vom Frontend genutzte Schluessel ist der Anzeigename; Code/Name aus
        # der API behalten wir zur Info.
        stats[display_name] = data
        print(f"  OK {display_name:<20} via {used!r:<20} "
              f"Arten={data.get('speciesCount')} Funde={data.get('observationCount')} "
              f"TopKaefer={len(data.get('topBeetles') or [])}")
        time.sleep(0.1)  # hoeflich zum Backend

    if not stats:
        print("\nFEHLER: Keine Laenderdaten erhalten. Ist das Backend (mit erweiterter "
              "/api/countries-Antwort) erreichbar?", file=sys.stderr)
        return 1

    banner = (
        "// AUTO-GENERIERT von backend/scripts/gen_country_stats.py - NICHT von Hand editieren.\n"
        f"// Quelle: {base}/api/countries/  |  Laender: {len(stats)}"
        + (f"  |  ohne Daten: {', '.join(missing)}" if missing else "")
        + "\n"
    )
    payload = json.dumps(stats, ensure_ascii=False, indent=2)
    OUTPUT.write_text(f"{banner}window.COUNTRY_STATS = {payload};\n", encoding="utf-8")

    print(f"\nGeschrieben: {OUTPUT}  ({len(stats)} Laender"
          + (f", {len(missing)} ohne Daten" if missing else "") + ")")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
