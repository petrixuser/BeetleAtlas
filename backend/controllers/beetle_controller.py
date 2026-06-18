from typing import Any, Dict, List, Optional

from backend.controllers.core_controller import (
    parse_bbox_or_error,
    raise_api_error,
    resolve_order_clause_or_error,
    validate_pagination_or_error,
)

from backend.config.beetle_filters import ADVANCED_FILTER_KEYS
from backend.config.country_mappings import COUNTRY_CODE_TO_LOCATION_NAME
from backend.core.beetle_filter_helpers import apply_exact_filters
from backend.core.payloads import to_beetle_payload
from backend.repositories.beetle_repository import (
    fetch_beetle_detail_row,
    fetch_beetle_media_rows,
    fetch_beetle_media_rows_total,
    fetch_beetles_list_lean,
    fetch_beetles_list_rows_total,
    fetch_country_detail_rows,
)

def list_beetles_controller(
    q: Optional[str],
    climate: Optional[str],
    vegetation: Optional[str],
    elevation: Optional[str],
    temperature_band: Optional[str],
    precipitation_band: Optional[str],
    soil_moisture_band: Optional[str],
    ndvi_band: Optional[str],
    humidity_band: Optional[str],
    pressure_band: Optional[str],
    light_pollution_band: Optional[str],
    slope_band: Optional[str],
    water_distance_band: Optional[str],
    human_impact_band: Optional[str],
    landcover_group: Optional[str],
    coordinate_uncertainty_band: Optional[str],
    soil_ph_band: Optional[str],
    soil_carbon_band: Optional[str],
    worldclim_temp_band: Optional[str],
    worldclim_precip_band: Optional[str],
    event_date_quality: Optional[str],
    basis_of_record_class: Optional[str],
    taxon_resolution: Optional[str],
    media_coverage: Optional[str],
    license_class: Optional[str],
    bbox: Optional[str],
    limit: int,
    offset: int,
    sort_by: str,
    sort_dir: str,
):
    """Return a paginated beetle list using base and advanced filters plus optional bbox.

    Uses a lean query path when no advanced filters are active.
    """
    validate_pagination_or_error(limit, offset)

    order_by_sql = resolve_order_clause_or_error(
        sort_by,
        sort_dir,
        {
            "id": "e.gbif_id",
            "name": "e.name",
            "family": "e.family",
            "observedAt": "e.observedAt",
            "elevation": "e.elevation",
            "temperature": "e.temperature",
            "climate": "e.climate",
            "vegetation": "e.vegetation",
        },
    )

    filters: List[str] = []
    base_filters: List[str] = []
    params: Dict[str, Any] = {"offset": offset}
    requested_filters: Dict[str, Optional[str]] = {
        "climate": climate,
        "vegetation": vegetation,
        "elevation": elevation,
        "temperature_band": temperature_band,
        "precipitation_band": precipitation_band,
        "soil_moisture_band": soil_moisture_band,
        "ndvi_band": ndvi_band,
        "humidity_band": humidity_band,
        "pressure_band": pressure_band,
        "light_pollution_band": light_pollution_band,
        "slope_band": slope_band,
        "water_distance_band": water_distance_band,
        "human_impact_band": human_impact_band,
        "landcover_group": landcover_group,
        "coordinate_uncertainty_band": coordinate_uncertainty_band,
        "soil_ph_band": soil_ph_band,
        "soil_carbon_band": soil_carbon_band,
        "worldclim_temp_band": worldclim_temp_band,
        "worldclim_precip_band": worldclim_precip_band,
        "event_date_quality": event_date_quality,
        "basis_of_record_class": basis_of_record_class,
        "taxon_resolution": taxon_resolution,
        "media_coverage": media_coverage,
        "license_class": license_class,
    }

    if q:
        filters.append(
            """
            (
                e.name LIKE :q
                OR e.family LIKE :q
                OR e.location LIKE :q
            )
            """
        )
        params["q"] = f"%{q.strip()}%"

    apply_exact_filters(filters, params, requested_filters)

    if bbox:
        bbox_params = parse_bbox_or_error(bbox)
        base_filters.append("(l.longitude BETWEEN :min_lng AND :max_lng AND l.latitude BETWEEN :min_lat AND :max_lat)")
        params.update(bbox_params)

    where_sql = ""
    if filters:
        where_sql = "WHERE " + " AND ".join(filters)

    base_where_sql = ""
    if base_filters:
        base_where_sql = "WHERE " + " AND ".join(base_filters)

    has_advanced_filters = any(requested_filters.get(key) for key in ADVANCED_FILTER_KEYS)
    fetch = fetch_beetles_list_rows_total if has_advanced_filters else fetch_beetles_list_lean
    rows, total = fetch(
        where_sql=where_sql,
        base_where_sql=base_where_sql,
        order_by_sql=order_by_sql,
        limit=limit,
        offset=offset,
        params=params,
    )

    page = (offset // limit) + 1
    return {
        "items": [to_beetle_payload(dict(row)) for row in rows],
        "total": int(total),
        "page": page,
        "page_size": limit,
    }

def get_beetle_by_id_controller(beetle_id: str):
    """Retrieves detailed information about a specific beetle observation by its ID, including associated media, and returns it in a structured payload format."""
    normalized = beetle_id.strip()
    if normalized.startswith("occ-"):
        normalized = normalized[4:]

    if not normalized.isdigit():
        raise_api_error(400, "invalid_id", "Invalid ID. Expected e.g. occ-123 or 123.")

    row = fetch_beetle_detail_row(int(normalized))

    if row is None:
        raise_api_error(404, "not_found", "No entry found for this ID.")

    payload = to_beetle_payload(row)
    media_rows = fetch_beetle_media_rows(int(normalized), limit=8)
    payload.setdefault("meta", {}).setdefault("media", {})["items"] = [
        {
            "url": item.get("image_url"),
            "license": item.get("license"),
            "creator": item.get("creator"),
            "publisher": item.get("publisher"),
            "rightsHolder": item.get("rights_holder"),
        }
        for item in media_rows
    ]
    if media_rows and not payload.get("imageUrl"):
        payload["imageUrl"] = media_rows[0].get("image_url")

    return payload

def get_country_detail_controller(country_code: str):
    """Return aggregated country details for a country code.

    Includes species count, top climates and vegetations, and elevation range.
    """
    normalized = country_code.strip().upper()
    if not normalized:
        raise_api_error(400, "invalid_country_code", "Country code must not be empty.")

    lookup_value = COUNTRY_CODE_TO_LOCATION_NAME.get(normalized, normalized)

    overview, climates, vegetations = fetch_country_detail_rows(lookup_value)

    if overview is None or (overview.get("species_count") or 0) == 0:
        raise_api_error(404, "not_found", "No data found for this country code.")

    min_elev = overview.get("min_elevation")
    max_elev = overview.get("max_elevation")
    elevation_range = [
        int(round(min_elev)) if min_elev is not None else None,
        int(round(max_elev)) if max_elev is not None else None,
    ]

    return {
        "code": normalized,
        "name": overview.get("country_name") or lookup_value,
        "speciesCount": int(overview.get("species_count") or 0),
        "topClimates": [row["climate"] for row in climates],
        "topVegetations": [row["vegetation"] for row in vegetations],
        "elevationRange": elevation_range,
    }

def get_beetle_media_controller(beetle_id: str, limit: int, offset: int):
    """Retrieves a paginated list of media items associated with a specific beetle observation, identified by its ID, and returns them in a structured format."""
    validate_pagination_or_error(limit, offset)

    normalized = beetle_id.strip()
    if normalized.startswith("occ-"):
        normalized = normalized[4:]

    if not normalized.isdigit():
        raise_api_error(400, "invalid_id", "Invalid ID. Expected e.g. occ-123 or 123.")

    gbif_id = int(normalized)
    detail_row = fetch_beetle_detail_row(gbif_id)
    if detail_row is None:
        raise_api_error(404, "not_found", "No entry found for this ID.")

    rows, total = fetch_beetle_media_rows_total(gbif_id=gbif_id, limit=limit, offset=offset)

    page = (offset // limit) + 1
    return {
        "id": f"occ-{gbif_id}",
        "items": [
            {
                "mediaId": row.get("media_id"),
                "url": row.get("image_url"),
                "license": row.get("license"),
                "creator": row.get("creator"),
                "publisher": row.get("publisher"),
                "rightsHolder": row.get("rights_holder"),
                "references": row.get("references"),
            }
            for row in rows
        ],
        "total": total,
        "page": page,
        "page_size": limit,
    }
