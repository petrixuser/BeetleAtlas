import argparse
import math
from collections import defaultdict
from pathlib import Path

import pandas as pd


FIELDS = [
    "avg_temperature",
    "precipitation",
    "soil_moisture",
    "ndvi",
    "relative_humidity",
    "surface_pressure_hpa",
    "nighttime_lights",
]


def normalize_location_id(series: pd.Series) -> pd.Series:
    s = series.astype(str).str.strip()
    n = pd.to_numeric(s, errors="coerce")
    out = s.copy()
    mask = n.notna()
    out.loc[mask] = n.loc[mask].round().astype("Int64").astype(str)
    out = out.str.replace(r"\\.0+$", "", regex=True)
    out = out.replace({"<NA>": "", "nan": "", "None": ""})
    return out


def normalize_snapshot_date(series: pd.Series) -> pd.Series:
    raw = series.astype(str).str.strip()
    dt = pd.to_datetime(raw, errors="coerce")

    ym_mask = raw.str.match(r"^[0-9]{4}-[0-9]{2}$", na=False)
    dt.loc[ym_mask] = pd.to_datetime(raw.loc[ym_mask] + "-01", errors="coerce")

    return dt.dt.strftime("%Y-%m-%d")


def to_numeric_with_nan(series: pd.Series) -> pd.Series:
    s = pd.to_numeric(series, errors="coerce")
    s.loc[s <= -9999] = pd.NA
    return s


def haversine_km(lat1, lon1, lat2, lon2):
    r = 6371.0
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(math.radians(lat1))
        * math.cos(math.radians(lat2))
        * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return r * c


def build_spatial_index(group_df: pd.DataFrame, value_col: str, cell_deg: float):
    donors = group_df[group_df[value_col].notna()].copy()
    grid = defaultdict(list)

    for idx, row in donors.iterrows():
        gx = int(math.floor(row["latitude"] / cell_deg))
        gy = int(math.floor(row["longitude"] / cell_deg))
        grid[(gx, gy)].append(idx)

    return donors, grid


def find_nearest_donor_idx(row, donors, grid, radius_km, cell_deg):
    lat = row["latitude"]
    lon = row["longitude"]

    if pd.isna(lat) or pd.isna(lon):
        return None

    radius_deg = radius_km / 111.0
    steps = max(1, int(math.ceil(radius_deg / cell_deg)))
    cx = int(math.floor(lat / cell_deg))
    cy = int(math.floor(lon / cell_deg))

    best_idx = None
    best_dist = None

    for dx in range(-steps, steps + 1):
        for dy in range(-steps, steps + 1):
            candidates = grid.get((cx + dx, cy + dy), [])
            for idx in candidates:
                drow = donors.loc[idx]
                dist = haversine_km(lat, lon, drow["latitude"], drow["longitude"])
                if dist <= radius_km and (best_dist is None or dist < best_dist):
                    best_idx = idx
                    best_dist = dist

    return best_idx


def fill_missing_by_nearest(df: pd.DataFrame, fields, radius_km: float):
    cell_deg = max(radius_km / 111.0, 0.05)
    fill_counts = {field: 0 for field in fields}

    for field in fields:
        for snapshot_date, g in df.groupby("snapshot_date"):
            donors, grid = build_spatial_index(g, field, cell_deg)
            if donors.empty:
                continue

            missing_idx = g[g[field].isna()].index.tolist()
            for idx in missing_idx:
                row = df.loc[idx]
                donor_idx = find_nearest_donor_idx(row, donors, grid, radius_km, cell_deg)
                if donor_idx is None:
                    continue

                df.at[idx, field] = donors.at[donor_idx, field]
                fill_counts[field] += 1

    return fill_counts


def fill_nighttime_lights_by_same_location_nearest_date(df: pd.DataFrame) -> int:
    field = "nighttime_lights"
    if field not in df.columns:
        return 0

    work = df.copy()
    work["_snapshot_dt"] = pd.to_datetime(work["snapshot_date"], errors="coerce")
    valid_date = work["_snapshot_dt"].notna()
    if not valid_date.any():
        return 0

    filled = 0
    grouped = work[valid_date].groupby("location_id", sort=False)
    for _, idx in grouped.groups.items():
        loc_idx = pd.Index(idx)
        loc_view = work.loc[loc_idx].sort_values("_snapshot_dt")

        known = loc_view[loc_view[field].notna()]
        if known.empty:
            continue

        known_dates = known["_snapshot_dt"]
        known_vals = known[field]

        missing = loc_view[loc_view[field].isna()]
        for miss_idx, miss_row in missing.iterrows():
            target = miss_row["_snapshot_dt"]
            pos = known_dates.searchsorted(target)

            candidates = []
            if pos > 0:
                left_idx = known_dates.index[pos - 1]
                candidates.append((abs(target - known_dates.loc[left_idx]), left_idx))
            if pos < len(known_dates):
                right_idx = known_dates.index[pos]
                candidates.append((abs(known_dates.loc[right_idx] - target), right_idx))

            if not candidates:
                continue

            _, donor_idx = min(candidates, key=lambda x: x[0])
            donor_val = known_vals.loc[donor_idx]
            if pd.isna(donor_val):
                continue

            df.at[miss_idx, field] = donor_val
            filled += 1

    return filled


def main():
    parser = argparse.ArgumentParser(
        description="Fill missing climate values from nearest location within a radius per snapshot_date."
    )
    parser.add_argument(
        "--input",
        default="csv/climate_snapshot_import.csv",
        help="Input climate snapshot CSV.",
    )
    parser.add_argument(
        "--locations",
        default="csv/ee_location_dates_dynamic.csv",
        help="CSV with location/date and coordinates.",
    )
    parser.add_argument(
        "--output",
        default="csv/climate_snapshot_import_filled_nearest.csv",
        help="Output CSV path.",
    )
    parser.add_argument(
        "--radius-km",
        type=float,
        default=50.0,
        help="Max distance for neighbor fill in kilometers.",
    )
    args = parser.parse_args()

    input_path = Path(args.input)
    locations_path = Path(args.locations)
    output_path = Path(args.output)

    climate = pd.read_csv(input_path, low_memory=False)
    locs = pd.read_csv(locations_path, usecols=["location_id", "date", "latitude", "longitude"])

    climate["location_id"] = normalize_location_id(climate["location_id"])
    climate["snapshot_date"] = normalize_snapshot_date(climate["snapshot_date"])

    locs["location_id"] = normalize_location_id(locs["location_id"])
    locs["snapshot_date"] = normalize_snapshot_date(locs["date"])

    locs = locs[["location_id", "snapshot_date", "latitude", "longitude"]].dropna(
        subset=["snapshot_date", "latitude", "longitude"]
    )

    for field in FIELDS:
        if field in climate.columns:
            climate[field] = to_numeric_with_nan(climate[field])

    df = climate.merge(
        locs,
        on=["location_id", "snapshot_date"],
        how="left",
    )

    fill_counts = fill_missing_by_nearest(df, [f for f in FIELDS if f in df.columns], args.radius_km)
    temporal_nl_fills = fill_nighttime_lights_by_same_location_nearest_date(df)

    out_cols = [
        "location_id",
        "snapshot_date",
        "avg_temperature",
        "precipitation",
        "soil_moisture",
        "ndvi",
        "relative_humidity",
        "surface_pressure_hpa",
        "nighttime_lights",
    ]

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df[out_cols].to_csv(output_path, index=False)

    print(f"Input rows: {len(climate)}")
    print(f"Output rows: {len(df)}")
    print(f"Radius km: {args.radius_km}")
    for field, count in fill_counts.items():
        print(f"filled_{field}: {count}")
    print(f"filled_nighttime_lights_temporal_same_location: {temporal_nl_fills}")
    print(f"Output: {output_path}")


if __name__ == "__main__":
    main()
