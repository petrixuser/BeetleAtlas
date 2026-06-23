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


def normalize_measurement(raw_value):
    value = (raw_value or "").strip()
    if value == "":
        return ""

    lowered = value.lower()
    if lowered in {"nan", "null", "none"}:
        return ""

    try:
        num = float(value)
    except ValueError:
        return value

    # Earth Engine no-data values are often encoded as -9999.
    if num <= -9999:
        return ""

    return value


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


def load_expected_keys(expected_keys_csv):
    path = Path(expected_keys_csv)
    if not path.exists():
        return set(), False

    keys = set()
    with path.open("r", encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        for row in reader:
            location_id = (row.get("location_id") or "").strip()
            raw_date = first_non_empty(row, ["date", "ym", "snapshot_date"])
            snapshot_date = normalize_snapshot_date(raw_date)
            if not location_id or not snapshot_date:
                continue
            keys.add((location_id, snapshot_date))

    return keys, True


def merge_dynamic_exports(input_dir, output_file, expected_keys_csv=None):
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

                avg_temperature = normalize_measurement(first_non_empty(row, ["avg_temperature"]))
                precipitation = normalize_measurement(first_non_empty(row, ["precipitation"]))
                soil_moisture = normalize_measurement(first_non_empty(row, ["soil_moisture"]))
                ndvi = normalize_measurement(first_non_empty(row, ["ndvi"]))
                relative_humidity = normalize_measurement(first_non_empty(row, ["relative_humidity", "humidity"]))
                surface_pressure = normalize_measurement(first_non_empty(row, ["surface_pressure_hpa", "surface_pressure"]))
                nighttime_lights = normalize_measurement(first_non_empty(row, ["nighttime_lights"]))

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

    expected_key_count = None
    if expected_keys_csv:
        expected_keys, found = load_expected_keys(expected_keys_csv)
        if found:
            expected_key_count = len(expected_keys)
            for location_id, snapshot_date in expected_keys:
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
        else:
            print(f"Warnung: expected keys file nicht gefunden, ueberspringe Coverage-Fuellung: {expected_keys_csv}")

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
    if expected_key_count is not None:
        print(f"Expected key rows (from EE location/date file): {expected_key_count}")
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
    parser.add_argument(
        "--expected-keys-csv",
        default="csv/ee_location_dates_dynamic.csv",
        help=(
            "Optional CSV with expected location/date keys to guarantee full coverage "
            "(default: csv/ee_location_dates_dynamic.csv)."
        ),
    )
    args = parser.parse_args()

    input_folder = Path(args.input_dir) if args.input_dir else find_default_input_folder()
    output_csv = Path(args.output)
    merge_dynamic_exports(input_folder, output_csv, args.expected_keys_csv)
