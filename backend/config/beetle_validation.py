from backend.config.country_mappings import COUNTRY_CODE_TO_LOCATION_NAME


GBIF_BASIS_OF_RECORD = {
    "HUMAN_OBSERVATION",
    "MACHINE_OBSERVATION",
    "PRESERVED_SPECIMEN",
}

LATAM_MIN_LAT = -56.0
LATAM_MAX_LAT = 33.5
LATAM_MIN_LON = -118.5
LATAM_MAX_LON = -30.0


LATAM_COUNTRY_CODES = {
    code
    for code in COUNTRY_CODE_TO_LOCATION_NAME
    if code != "US"
}

LATAM_COUNTRY_NAMES = {
    name.upper().strip()
    for code, name in COUNTRY_CODE_TO_LOCATION_NAME.items()
    if code in LATAM_COUNTRY_CODES
}


def coordinates_in_latam_bounds(latitude: float, longitude: float) -> bool:
    return LATAM_MIN_LAT <= latitude <= LATAM_MAX_LAT and LATAM_MIN_LON <= longitude <= LATAM_MAX_LON


def country_in_latam(country_value: str) -> bool:
    normalized = country_value.strip().upper()
    if not normalized:
        return False
    return normalized in LATAM_COUNTRY_CODES or normalized in LATAM_COUNTRY_NAMES
