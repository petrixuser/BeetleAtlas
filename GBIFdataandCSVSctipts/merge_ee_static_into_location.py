import argparse
import csv
from glob import glob
from pathlib import Path
from typing import Dict, List, Optional


TARGET_FIELDS = [
    "elevation",
    "slope",
    "landcover_class",
    "soil_ph",
    "soil_organic_carbon",
    "worldclim_bio01",
    "worldclim_bio12",
    "distance_to_water_m",
    "ecoregion_id",
    "biome_id",
    "human_modification",
]


def parse_location_id(value: Optional[str]) -> Optional[str]:
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None
    try:
        return str(int(float(s)))
    except ValueError:
        return None


def parse_num(value: Optional[str]) -> Optional[float]:
    if value is None:
        return None
    s = str(value).strip()
    if not s:
        return None
    try:
        v = float(s)
    except ValueError:
        return None
    if v == -9999:
        return None
    return v


def format_value(field: str, value: Optional[float]) -> str:
    if value is None:
        return ""

    # Convert OpenLandMap / WorldClim encoded values to physical units.
    if field == "soil_ph":
        if value > 14:
            value = value / 10.0
    elif field == "soil_organic_carbon":
        if value > 60:
            value = value / 5.0
    elif field == "worldclim_bio01":
        if value > 80:
            value = value / 10.0

    if field in {"landcover_class", "ecoregion_id", "biome_id"}:
        return str(int(round(value)))

    text = f"{value:.6f}".rstrip("0").rstrip(".")
    return text if text else "0"


def load_static_rows(static_files: List[str]) -> Dict[str, Dict[str, str]]:
    merged: Dict[str, Dict[str, str]] = {}

    for file_path in static_files:
        with open(file_path, "r", encoding="utf-8", newline="") as fin:
            reader = csv.DictReader(fin)
            for row in reader:
                location_id = parse_location_id(row.get("location_id"))
                if not location_id:
                    continue

                if location_id not in merged:
                    merged[location_id] = {k: "" for k in TARGET_FIELDS}

                rec = merged[location_id]
                for field in TARGET_FIELDS:
                    value = format_value(field, parse_num(row.get(field)))
                    if value != "":
                        rec[field] = value

    return merged


def merge_into_location_csv(location_csv: Path, static_values: Dict[str, Dict[str, str]]) -> int:
    with location_csv.open("r", encoding="utf-8", newline="") as fin:
        reader = csv.DictReader(fin)
        input_fields = reader.fieldnames or []
        rows = list(reader)

    output_fields = list(input_fields)
    for field in TARGET_FIELDS:
        if field not in output_fields:
            output_fields.append(field)

    updated = 0
    for row in rows:
        location_id = parse_location_id(row.get("location_id"))
        if not location_id:
            continue

        for field in TARGET_FIELDS:
            row.setdefault(field, "")

        static_row = static_values.get(location_id)
        if not static_row:
            continue

        touched = False
        for field in TARGET_FIELDS:
            if static_row[field] != "" and row.get(field, "").strip() == "":
                row[field] = static_row[field]
                touched = True

        if touched:
            updated += 1

    with location_csv.open("w", encoding="utf-8", newline="") as fout:
        writer = csv.DictWriter(fout, fieldnames=output_fields)
        writer.writeheader()
        writer.writerows(rows)

    return updated


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Merge Earth Engine static export batches into location.csv"
    )
    parser.add_argument(
        "--location-csv",
        default="Database/CSV's/location.csv",
        help="Path to location.csv",
    )
    parser.add_argument(
        "--static-glob",
        default="Database/CSV's/**/beetle_static_batch_*.csv",
        help="Glob pattern for static batch CSV files",
    )

    args = parser.parse_args()
    location_csv = Path(args.location_csv)
    static_files = sorted(glob(args.static_glob, recursive=True))

    if not location_csv.exists():
        raise FileNotFoundError(f"location.csv not found: {location_csv}")
    if not static_files:
        raise FileNotFoundError(f"No static files found for pattern: {args.static_glob}")

    static_values = load_static_rows(static_files)
    updated = merge_into_location_csv(location_csv, static_values)

    print(f"Static files read: {len(static_files)}")
    print(f"Locations with static data: {len(static_values)}")
    print(f"Rows updated in location.csv: {updated}")


if __name__ == "__main__":
    main()
