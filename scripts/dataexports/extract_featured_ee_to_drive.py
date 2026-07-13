"""Erzeugt die Earth-Engine-Input-CSVs fuer die hervorgehobenen Kaefer (featured beetles).

Aus der Frontend-Liste featured-beetles.js werden zwei CSVs abgeleitet: eine
statische (ein Punkt pro location_id) und eine dynamische (ein Punkt pro
location_id + Monat). Diese dienen als Eingabe fuer extract_ee_to_drive.py.
"""

import argparse
import json
import re
from pathlib import Path

import pandas as pd


DEFAULT_FEATURED_JS = "../frontend/data/featured-beetles.js"
DEFAULT_STATIC_OUT = "csv/ee_featured_locations_static.csv"
DEFAULT_DYNAMIC_OUT = "csv/ee_featured_location_dates_dynamic.csv"


def load_featured_entries(featured_js_path: Path):
    """Liest das FEATURED_BEETLES-Array aus featured-beetles.js und liefert es als Liste."""
    raw = featured_js_path.read_text(encoding="utf-8")
    start = raw.find("[")
    end = raw.rfind("];\n")
    if end == -1:
        end = raw.rfind("];")

    if start == -1 or end == -1:
        raise ValueError("Konnte Array in featured-beetles.js nicht finden.")

    arr_text = raw[start : end + 1]
    return json.loads(arr_text)


def parse_year_month(value):
    """Extrahiert 'YYYY-MM' aus einem beliebigen Datumstext (oder None, falls nicht gefunden)."""
    text = str(value or "").strip()
    match = re.search(r"(\d{4}-\d{2})", text)
    return match.group(1) if match else None


def build_featured_csvs(featured_js, static_out, dynamic_out):
    """Schreibt aus der Featured-Liste die statische und dynamische EE-Input-CSV."""
    entries = load_featured_entries(featured_js)

    static_rows = []
    dynamic_rows = []

    for item in entries:
        location_id = str(item.get("id") or "").strip()
        coords = item.get("coordinates") or []
        if len(coords) != 2:
            continue

        lon, lat = coords
        static_rows.append(
            {
                "location_id": location_id,
                "latitude": lat,
                "longitude": lon,
            }
        )

        ym = parse_year_month(item.get("observedAt"))
        if ym:
            dynamic_rows.append(
                {
                    "location_id": location_id,
                    "latitude": lat,
                    "longitude": lon,
                    "date": ym,
                }
            )

    static_df = pd.DataFrame(static_rows).drop_duplicates(subset=["location_id"])
    dynamic_df = pd.DataFrame(dynamic_rows).drop_duplicates(subset=["location_id", "date"])

    static_out.parent.mkdir(parents=True, exist_ok=True)
    dynamic_out.parent.mkdir(parents=True, exist_ok=True)

    static_df.to_csv(static_out, index=False)
    dynamic_df.to_csv(dynamic_out, index=False)

    print(f"Featured entries: {len(entries)}")
    print(f"Static rows written: {len(static_df)} -> {static_out}")
    print(f"Dynamic rows written: {len(dynamic_df)} -> {dynamic_out}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Build EE input CSVs for featured beetles.")
    parser.add_argument("--featured-js", default=DEFAULT_FEATURED_JS)
    parser.add_argument("--static-out", default=DEFAULT_STATIC_OUT)
    parser.add_argument("--dynamic-out", default=DEFAULT_DYNAMIC_OUT)
    args = parser.parse_args()

    build_featured_csvs(
        featured_js=Path(args.featured_js),
        static_out=Path(args.static_out),
        dynamic_out=Path(args.dynamic_out),
    )
