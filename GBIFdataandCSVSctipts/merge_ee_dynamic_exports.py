import csv
import argparse
import re
from pathlib import Path


def first_non_empty(row, keys):
    for key in keys:
        value = (row.get(key) or "").strip()
        if value != "":
            return value
    return ""


def normalize_snapshot_date(raw_date):
    raw_date = (raw_date or "").strip()
    if not raw_date:
        return ""

    # Accept YYYY-MM-DD
    if re.match(r"^\d{4}-\d{2}-\d{2}$", raw_date):
        return raw_date

    # Accept YYYY-MM
    if re.match(r"^\d{4}-\d{2}$", raw_date):
        return f"{raw_date}-01"

    # Accept YYYY
    if re.match(r"^\d{4}$", raw_date):
        return f"{raw_date}-01-01"

    return ""


def merge_dynamic_exports(input_dir, output_file):
    input_path = Path(input_dir)
    output_path = Path(output_file)

    if not input_path.exists():
        raise FileNotFoundError(f"Input folder not found: {input_path}")

    files = sorted(input_path.glob("*.csv"))
    if not files:
        raise FileNotFoundError(f"No CSV files found in: {input_path}")

    merged = {}
    valid_files = 0

    for file in files:
        with file.open("r", encoding="utf-8", newline="") as f:
            reader = csv.DictReader(f)
            if not reader.fieldnames:
                continue

            headers = set(reader.fieldnames)
            # Keep only files that look like dynamic EE outputs.
            if "location_id" not in headers:
                continue
            if not ({"date", "ym", "snapshot_date"} & headers):
                continue

            valid_files += 1

            for row in reader:
                location_id = (row.get("location_id") or "").strip()
                raw_date = first_non_empty(row, ["date", "ym", "snapshot_date"])
                snapshot_date = normalize_snapshot_date(raw_date)

                if not location_id or not snapshot_date:
                    continue

                key = (location_id, snapshot_date)
                if key not in merged:
                    merged[key] = {
                        "location_id": location_id,
                        "snapshot_date": snapshot_date,
                        "avg_temperature": "",
                        "precipitation": "",
                        "soil_moisture": "",
                        "ndvi": "",
                        "relative_humidity": "",
                        "surface_pressure_hpa": "",
                        "nighttime_lights": "",
                    }

                rec = merged[key]

                avg_temperature = first_non_empty(row, ["avg_temperature"])
                precipitation = first_non_empty(row, ["precipitation"])
                soil_moisture = first_non_empty(row, ["soil_moisture"])
                ndvi = first_non_empty(row, ["ndvi"])
                relative_humidity = first_non_empty(row, ["relative_humidity", "humidity"])
                surface_pressure = first_non_empty(row, ["surface_pressure_hpa", "surface_pressure"])
                nighttime_lights = first_non_empty(row, ["nighttime_lights"])

                if rec["avg_temperature"] == "" and avg_temperature != "":
                    rec["avg_temperature"] = avg_temperature
                if rec["precipitation"] == "" and precipitation != "":
                    rec["precipitation"] = precipitation
                if rec["soil_moisture"] == "" and soil_moisture != "":
                    rec["soil_moisture"] = soil_moisture
                if rec["ndvi"] == "" and ndvi != "":
                    rec["ndvi"] = ndvi
                if rec["relative_humidity"] == "" and relative_humidity != "":
                    rec["relative_humidity"] = relative_humidity
                if rec["surface_pressure_hpa"] == "" and surface_pressure != "":
                    rec["surface_pressure_hpa"] = surface_pressure
                if rec["nighttime_lights"] == "" and nighttime_lights != "":
                    rec["nighttime_lights"] = nighttime_lights

    if valid_files == 0:
        raise ValueError(
            "No dynamic EE CSV files detected. Expected columns: location_id + date/ym/snapshot_date."
        )

    rows = sorted(
        merged.values(),
        key=lambda r: (int(r["location_id"]) if r["location_id"].isdigit() else r["location_id"], r["snapshot_date"]),
    )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "location_id",
                "snapshot_date",
                "avg_temperature",
                "precipitation",
                "soil_moisture",
                "ndvi",
                "relative_humidity",
                "surface_pressure_hpa",
                "nighttime_lights",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    print(f"Files scanned: {len(files)}")
    print(f"Dynamic files used: {valid_files}")
    print(f"Merged rows: {len(rows)}")
    print(f"Output: {output_path}")


def find_default_input_folder():
    candidates = [
        Path("beetle_exports"),
        Path("ee_exports/dynamic"),
    ]

    for candidate in candidates:
        if candidate.exists() and any(candidate.glob("*.csv")):
            return candidate

    return Path("beetle_exports")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Merge Earth Engine dynamic export CSV files into one climate import CSV."
    )
    parser.add_argument(
        "--input-dir",
        default=None,
        help="Folder with dynamic EE CSV files (default: beetle_exports if present, else ee_exports/dynamic).",
    )
    parser.add_argument(
        "--output",
        default="csv/climate_snapshot_import.csv",
        help="Output merged CSV path.",
    )
    args = parser.parse_args()

    input_folder = Path(args.input_dir) if args.input_dir else find_default_input_folder()
    output_csv = Path(args.output)
    merge_dynamic_exports(input_folder, output_csv)
