import csv
import re
from pathlib import Path

# Input files must be in the same folder as this script:
# - occurrence.txt
# - multimedia.txt
# Output CSVs are written to ./csv/

BASE_DIR = Path(__file__).resolve().parent
OUTPUT_DIR = BASE_DIR / "csv"
OUTPUT_DIR.mkdir(exist_ok=True)

OCCURRENCE_FILE = BASE_DIR / "occurrence.txt"
MULTIMEDIA_FILE = BASE_DIR / "multimedia.txt"


def clean(value: str) -> str:
    return (value or "").strip()

def norm(value: str) -> str:
    return clean(value).lower()


def valid_coord(lat: str, lon: str) -> bool:
    try:
        lat_f = float(lat)
        lon_f = float(lon)
        return -90 <= lat_f <= 90 and -180 <= lon_f <= 180
    except (TypeError, ValueError):
        return False


def year_month_from_event_date(event_date: str) -> str:
    """Return YYYY-MM from GBIF/DarwinCore eventDate if possible."""
    event_date = clean(event_date)
    if not event_date:
        return ""

    # Handles: 2021-05-13, 2021-05, 2021, 2021-05-01/2021-05-04
    match = re.search(r"(\d{4})(?:-(\d{2}))?", event_date)
    if not match:
        return ""

    year = match.group(1)
    month = match.group(2)
    if not month:
        return ""
    return f"{year}-{month}"


def location_key_from_row(row: dict) -> tuple:
    """
    Dedupe locations by exact coordinates + locality fields.
    Keep exact coordinate strings; do not round here unless you intentionally want coarser grouping.
    """
    city = clean(row.get("county")) or clean(row.get("municipality"))
    return (
        norm(row.get("decimalLatitude")),
        norm(row.get("decimalLongitude")),
        norm(row.get("country")),
        norm(row.get("stateProvince")),
        norm(city),
        norm(row.get("verbatimLocality")),
    )


def read_occurrences_and_build_tables():
    if not OCCURRENCE_FILE.exists():
        raise FileNotFoundError(f"Nicht gefunden: {OCCURRENCE_FILE}")

    species_id_map = {}
    location_id_map = {}

    species_rows = []
    location_rows = []
    observation_rows = []

    with OCCURRENCE_FILE.open("r", encoding="utf-8", newline="") as fin:
        reader = csv.DictReader(fin, delimiter="\t")

        for row in reader:
            gbif_id = clean(row.get("gbifID"))
            lat = clean(row.get("decimalLatitude"))
            lon = clean(row.get("decimalLongitude"))

            if not gbif_id or not valid_coord(lat, lon):
                continue

            # ---- Species / Taxon ----
            taxon_id = clean(row.get("taxonID"))
            scientific_name = clean(row.get("scientificName"))

            # Stable surrogate key for DB FK.
            # Prefer taxon_id; fallback to scientific_name; last fallback uses gbif_id.
            species_key = taxon_id or scientific_name or f"missing_species_{gbif_id}"

            if species_key not in species_id_map:
                beetle_id = str(len(species_id_map) + 1)
                species_id_map[species_key] = beetle_id

                species_rows.append({
                    "beetle_id": beetle_id,
                    "taxon_id": taxon_id,
                    "family": clean(row.get("family")),
                    "genus": clean(row.get("genus")),
                    "specific_epithet": clean(row.get("specificEpithet")),
                    "scientific_name": scientific_name,
                    "scientific_name_authorship": clean(row.get("scientificNameAuthorship")),
                })

            beetle_id = species_id_map[species_key]

            # ---- Location ----
            loc_key = location_key_from_row(row)
            if loc_key not in location_id_map:
                location_id = str(len(location_id_map) + 1)
                location_id_map[loc_key] = location_id

                city = clean(row.get("county")) or clean(row.get("municipality"))
                location_rows.append({
                    "location_id": location_id,
                    "latitude": lat,
                    "longitude": lon,
                    "coordinate_uncertainty": clean(row.get("coordinateUncertaintyInMeters")),
                    "country": clean(row.get("country")),
                    "region": clean(row.get("stateProvince")),
                    "city": city,
                    "verbatim_locality": clean(row.get("verbatimLocality")),
                    # Filled later by Earth Engine static export / SQL import
                    "elevation": "",
                    "slope": "",
                    "landcover_class": "",
                    "soil_ph": "",
                    "soil_organic_carbon": "",
                    "worldclim_bio01": "",
                    "worldclim_bio12": "",
                    "distance_to_water_m": "",
                    "ecoregion_id": "",
                    "biome_id": "",
                    "human_modification": "",
                })

            location_id = location_id_map[loc_key]

            # ---- Observation ----
            observation_rows.append({
                "gbif_id": gbif_id,
                "recorded_by": clean(row.get("recordedBy")),
                "catalogue_number": clean(row.get("catalogNumber")),
                "identification_id": clean(row.get("identificationID")),
                "identified_by": clean(row.get("identifiedBy")),
                "beetle_id": beetle_id,
                "taxon_id": taxon_id,
                "location_id": location_id,
                "event_date": clean(row.get("eventDate")),
                "verbatim_event_date": clean(row.get("verbatimEventDate")) or clean(row.get("eventDate")),
                "basis_of_record": clean(row.get("basisOfRecord")),
                "dataset_name": clean(row.get("datasetName")),
                "institution_code": clean(row.get("institutionCode")),
                "image_available": "0",
            })

    return species_rows, location_rows, observation_rows


def read_media():
    if not MULTIMEDIA_FILE.exists():
        print(f"Warnung: {MULTIMEDIA_FILE} nicht gefunden. media.csv wird leer erstellt.")
        return [], set()

    media_rows = []
    gbif_ids_with_media = set()

    with MULTIMEDIA_FILE.open("r", encoding="utf-8", newline="") as fin:
        reader = csv.DictReader(fin, delimiter="\t")
        media_id = 1
        for row in reader:
            gbif_id = clean(row.get("gbifID"))
            image_url = clean(row.get("identifier"))  # identifier is the actual media URL in GBIF multimedia.txt
            if not gbif_id or not image_url:
                continue

            media_rows.append({
                "media_id": str(media_id),
                "gbif_id": gbif_id,
                "image_url": image_url,
                "references": clean(row.get("references")),
                "creator": clean(row.get("creator")),
                "publisher": clean(row.get("publisher")),
                "rights_holder": clean(row.get("rightsHolder")),
                "license": clean(row.get("license")),
            })
            gbif_ids_with_media.add(gbif_id)
            media_id += 1

    return media_rows, gbif_ids_with_media


def write_csv(filename: str, rows: list, fieldnames: list):
    path = OUTPUT_DIR / filename
    with path.open("w", encoding="utf-8", newline="") as fout:
        writer = csv.DictWriter(fout, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    print(f"{filename}: {len(rows)} Zeilen -> {path}")


def create_earth_engine_csvs(location_rows: list, observation_rows: list):
    # Static: one row per unique location
    static_rows = [
        {
            "location_id": r["location_id"],
            "latitude": r["latitude"],
            "longitude": r["longitude"],
        }
        for r in location_rows
    ]

    # Dynamic: one row per unique location_id + YYYY-MM
    loc_lookup = {r["location_id"]: (r["latitude"], r["longitude"]) for r in location_rows}
    dynamic_seen = set()
    dynamic_rows = []

    for obs in observation_rows:
        location_id = obs.get("location_id", "")
        ym = year_month_from_event_date(obs.get("event_date", ""))
        if not location_id or not ym:
            continue

        key = (location_id, ym)
        if key in dynamic_seen:
            continue
        dynamic_seen.add(key)

        lat, lon = loc_lookup[location_id]
        dynamic_rows.append({
            "location_id": location_id,
            "date": ym,
            "latitude": lat,
            "longitude": lon,
        })

    write_csv("ee_locations_static.csv", static_rows, ["location_id", "latitude", "longitude"])
    write_csv("ee_location_dates_dynamic.csv", dynamic_rows, ["location_id", "date", "latitude", "longitude"])


def main():
    species_rows, location_rows, observation_rows = read_occurrences_and_build_tables()
    media_rows, gbif_ids_with_media = read_media()

    # Mark observations with at least one media row
    for obs in observation_rows:
        if obs["gbif_id"] in gbif_ids_with_media:
            obs["image_available"] = "1"

    write_csv("beetle_species.csv", species_rows, [
        "beetle_id", "taxon_id", "family", "genus", "specific_epithet", "scientific_name", "scientific_name_authorship"
    ])

    write_csv("location.csv", location_rows, [
        "location_id", "latitude", "longitude", "coordinate_uncertainty", "country", "region", "city",
        "verbatim_locality", "elevation", "slope", "landcover_class", "soil_ph", "soil_organic_carbon",
        "worldclim_bio01", "worldclim_bio12", "distance_to_water_m", "ecoregion_id", "biome_id", "human_modification"
    ])

    write_csv("observation.csv", observation_rows, [
        "gbif_id", "recorded_by", "catalogue_number", "identification_id", "identified_by",
        "beetle_id", "taxon_id", "location_id", "event_date", "verbatim_event_date", "basis_of_record",
        "dataset_name", "institution_code", "image_available"
    ])

    write_csv("media.csv", media_rows, [
        "media_id", "gbif_id", "image_url", "references", "creator", "publisher", "rights_holder", "license"
    ])

    create_earth_engine_csvs(location_rows, observation_rows)


if __name__ == "__main__":
    main()
