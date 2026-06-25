import json
import re
from pathlib import Path

import numpy as np
import pandas as pd


def main() -> None:
    repo_root = Path(__file__).resolve().parents[1]
    source_path = repo_root / "frontend" / "data" / "featured-beetles.js"
    output_path = repo_root / "backend" / "data" / "featured_beetle_record_import.csv"
    location_path = repo_root / "backend" / "data" / "location.csv"
    climate_path = repo_root / "GBIFdataandCSVSctipts" / "csv" / "climate_snapshot_import.csv"

    text = source_path.read_text(encoding="utf-8")
    match = re.search(r"window\.FEATURED_BEETLES\s*=\s*(\[.*?\])\s*;", text, flags=re.S)
    if not match:
        raise RuntimeError("FEATURED_BEETLES array not found in frontend/data/featured-beetles.js")

    featured_items = json.loads(match.group(1))

    loc = pd.read_csv(location_path, low_memory=False)
    clim = pd.read_csv(climate_path, low_memory=False)

    loc["location_id"] = pd.to_numeric(loc["location_id"], errors="coerce").astype("Int64")
    loc["latitude"] = pd.to_numeric(loc["latitude"], errors="coerce")
    loc["longitude"] = pd.to_numeric(loc["longitude"], errors="coerce")

    clim["location_id"] = pd.to_numeric(clim["location_id"], errors="coerce").astype("Int64")
    clim["snapshot_date"] = pd.to_datetime(clim["snapshot_date"], errors="coerce", utc=True).dt.tz_localize(None)
    for field in [
        "avg_temperature",
        "precipitation",
        "soil_moisture",
        "ndvi",
        "relative_humidity",
        "surface_pressure_hpa",
        "nighttime_lights",
    ]:
        if field in clim.columns:
            clim[field] = pd.to_numeric(clim[field], errors="coerce")

    # Speed up nearest lookup for a small featured list.
    loc_valid = loc[loc["latitude"].notna() & loc["longitude"].notna()].copy()
    loc_lat = loc_valid["latitude"].to_numpy(dtype=float)
    loc_lng = loc_valid["longitude"].to_numpy(dtype=float)

    def nearest_location_row(lat: float | None, lng: float | None):
        if lat is None or lng is None or pd.isna(lat) or pd.isna(lng):
            return None
        d2 = (loc_lat - float(lat)) ** 2 + (loc_lng - float(lng)) ** 2
        if d2.size == 0:
            return None
        idx = int(np.argmin(d2))
        return loc_valid.iloc[idx]

    def nearest_climate_row(location_id, observed_at_text: str):
        if pd.isna(location_id):
            return None
        sub = clim[clim["location_id"] == location_id]
        if sub.empty:
            return None
        observed_dt = pd.to_datetime(observed_at_text, errors="coerce", utc=True)
        if not pd.isna(observed_dt):
            observed_dt = observed_dt.tz_localize(None)
        if pd.isna(observed_dt):
            # Fallback to the most recent available snapshot if date is unparsable.
            return sub.sort_values("snapshot_date").iloc[-1]
        date_delta = (sub["snapshot_date"] - observed_dt).abs()
        idx = date_delta.idxmin()
        return sub.loc[idx]

    rows = []
    for item in featured_items:
        scientific_name = str(item.get("name") or "").strip()
        name_parts = [part for part in scientific_name.split(" ") if part]
        genus = name_parts[0] if name_parts else ""
        specific_epithet = name_parts[1] if len(name_parts) > 1 else ""

        observed_at = str(item.get("observedAt") or "").strip()
        coordinates = item.get("coordinates") or [None, None]
        longitude = coordinates[0] if len(coordinates) > 0 else None
        latitude = coordinates[1] if len(coordinates) > 1 else None
        nearest_loc = nearest_location_row(latitude, longitude)
        location_id = nearest_loc.get("location_id") if nearest_loc is not None else pd.NA
        nearest_climate = nearest_climate_row(location_id, observed_at)

        image_url = str(item.get("imageUrl") or "").strip()
        image_available = 1 if image_url else 0

        common_name = str(item.get("commonName") or "").strip()
        note = str(item.get("note") or "").strip()
        notes_parts = []
        if common_name:
            notes_parts.append(f"commonName={common_name}")
        if note:
            notes_parts.append(note)
        notes_parts.append("source=frontend featured-beetles.js")
        notes = " | ".join(notes_parts)

        rows.append(
            {
                "scientific_name": scientific_name,
                "family": str(item.get("family") or "").strip(),
                "genus": genus,
                "specific_epithet": specific_epithet,
                "country": (str(nearest_loc.get("country") or "").strip() if nearest_loc is not None else ""),
                "location": str(item.get("location") or "").strip(),
                "notes": notes,
                "event_date": observed_at,
                "verbatim_event_date": observed_at,
                "basis_of_record": "HUMAN_OBSERVATION",
                "dataset_name": "featured-beetles.js",
                "institution_code": "BeetleAtlas Featured",
                "image_available": image_available,
                "image_url": image_url,
                "media_references": "",
                "media_creator": "",
                "media_publisher": "",
                "media_rights_holder": "",
                "media_license": "",
                "latitude": latitude,
                "longitude": longitude,
                "coordinate_uncertainty": (
                    str(nearest_loc.get("coordinate_uncertainty") or "").strip() if nearest_loc is not None else ""
                ),
                "region": (str(nearest_loc.get("region") or "").strip() if nearest_loc is not None else ""),
                "city": (str(nearest_loc.get("city") or "").strip() if nearest_loc is not None else ""),
                "verbatim_locality": str(item.get("location") or "").strip(),
                "elevation": item.get("elevation") if item.get("elevation") is not None else (nearest_loc.get("elevation") if nearest_loc is not None else None),
                "temperature": item.get("temperature") if item.get("temperature") is not None else (nearest_climate.get("avg_temperature") if nearest_climate is not None else None),
                "precipitation": nearest_climate.get("precipitation") if nearest_climate is not None else None,
                "soil_moisture": nearest_climate.get("soil_moisture") if nearest_climate is not None else None,
                "ndvi": nearest_climate.get("ndvi") if nearest_climate is not None else None,
                "relative_humidity": nearest_climate.get("relative_humidity") if nearest_climate is not None else None,
                "surface_pressure_hpa": nearest_climate.get("surface_pressure_hpa") if nearest_climate is not None else None,
                "nighttime_lights": nearest_climate.get("nighttime_lights") if nearest_climate is not None else None,
                "slope": nearest_loc.get("slope") if nearest_loc is not None else None,
                "distance_to_water_m": nearest_loc.get("distance_to_water_m") if nearest_loc is not None else None,
                "human_modification": nearest_loc.get("human_modification") if nearest_loc is not None else None,
                "landcover_class": nearest_loc.get("landcover_class") if nearest_loc is not None else None,
                "ecoregion_id": nearest_loc.get("ecoregion_id") if nearest_loc is not None else None,
                "biome_id": nearest_loc.get("biome_id") if nearest_loc is not None else None,
                "soil_ph": nearest_loc.get("soil_ph") if nearest_loc is not None else None,
                "soil_organic_carbon": nearest_loc.get("soil_organic_carbon") if nearest_loc is not None else None,
                "worldclim_bio01": nearest_loc.get("worldclim_bio01") if nearest_loc is not None else None,
                "worldclim_bio12": nearest_loc.get("worldclim_bio12") if nearest_loc is not None else None,
            }
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(output_path, index=False)

    print(f"Wrote {len(rows)} rows to {output_path}")


if __name__ == "__main__":
    main()
