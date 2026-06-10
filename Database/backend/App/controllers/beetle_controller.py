from typing import Any, Dict, List, Optional

from Database.Backend.App.controllers.core_controller import (
    parse_bbox_or_error,
    raise_api_error,
    resolve_order_clause_or_error,
    validate_pagination_or_error,
)

from Database.Backend.App.core.payloads import to_beetle_payload
from Database.Backend.App.repositories.beetle_repository import (
    fetch_beetle_detail_row,
    fetch_beetle_media_rows,
    fetch_beetle_media_rows_total,
    fetch_beetles_list_rows_total,
    fetch_country_detail_rows,
)


COUNTRY_CODE_TO_LOCATION_NAME = {
    "AR": "ARGENTINA",
    "BO": "BOLIVIA",
    "BR": "BRAZIL",
    "CL": "CHILE",
    "CO": "COLOMBIA",
    "CR": "COSTA RICA",
    "DO": "DOMINICAN REPUBLIC",
    "EC": "ECUADOR",
    "GF": "GF",
    "GT": "GUATEMALA",
    "HN": "HONDURAS",
    "MQ": "MQ",
    "MX": "MEXICO",
    "NI": "NICARAGUA",
    "PA": "PANAMA",
    "PE": "PERU",
    "PR": "PUERTO RICO",
    "UY": "URUGUAY",
    "US": "US",
    "VE": "VENEZUELA",
}


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

    if climate:
        filters.append("e.climate = :climate")
        params["climate"] = climate
    if vegetation:
        filters.append("e.vegetation = :vegetation")
        params["vegetation"] = vegetation
    if elevation:
        filters.append("e.elevationGroup = :elevation")
        params["elevation"] = elevation
    if temperature_band:
        filters.append("e.temperature_band = :temperature_band")
        params["temperature_band"] = temperature_band
    if precipitation_band:
        filters.append("e.precipitation_band = :precipitation_band")
        params["precipitation_band"] = precipitation_band
    if soil_moisture_band:
        filters.append("e.soil_moisture_band = :soil_moisture_band")
        params["soil_moisture_band"] = soil_moisture_band
    if ndvi_band:
        filters.append("e.ndvi_band = :ndvi_band")
        params["ndvi_band"] = ndvi_band
    if humidity_band:
        filters.append("e.humidity_band = :humidity_band")
        params["humidity_band"] = humidity_band
    if pressure_band:
        filters.append("e.pressure_band = :pressure_band")
        params["pressure_band"] = pressure_band
    if light_pollution_band:
        filters.append("e.light_pollution_band = :light_pollution_band")
        params["light_pollution_band"] = light_pollution_band
    if slope_band:
        filters.append("e.slope_band = :slope_band")
        params["slope_band"] = slope_band
    if water_distance_band:
        filters.append("e.water_distance_band = :water_distance_band")
        params["water_distance_band"] = water_distance_band
    if human_impact_band:
        filters.append("e.human_modification_band = :human_impact_band")
        params["human_impact_band"] = human_impact_band
    if landcover_group:
        filters.append("e.landcover_group = :landcover_group")
        params["landcover_group"] = landcover_group
    if coordinate_uncertainty_band:
        filters.append("e.coordinate_uncertainty_band = :coordinate_uncertainty_band")
        params["coordinate_uncertainty_band"] = coordinate_uncertainty_band
    if soil_ph_band:
        filters.append("e.soil_ph_band = :soil_ph_band")
        params["soil_ph_band"] = soil_ph_band
    if soil_carbon_band:
        filters.append("e.soil_carbon_band = :soil_carbon_band")
        params["soil_carbon_band"] = soil_carbon_band
    if worldclim_temp_band:
        filters.append("e.worldclim_temp_band = :worldclim_temp_band")
        params["worldclim_temp_band"] = worldclim_temp_band
    if worldclim_precip_band:
        filters.append("e.worldclim_precip_band = :worldclim_precip_band")
        params["worldclim_precip_band"] = worldclim_precip_band
    if event_date_quality:
        filters.append("e.event_date_quality = :event_date_quality")
        params["event_date_quality"] = event_date_quality
    if basis_of_record_class:
        filters.append("e.basis_of_record_class = :basis_of_record_class")
        params["basis_of_record_class"] = basis_of_record_class
    if taxon_resolution:
        filters.append("e.taxon_resolution = :taxon_resolution")
        params["taxon_resolution"] = taxon_resolution
    if media_coverage:
        filters.append("e.media_coverage = :media_coverage")
        params["media_coverage"] = media_coverage
    if license_class:
        filters.append("e.license_class = :license_class")
        params["license_class"] = license_class

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
    rows, total = fetch_beetles_list_rows_total(
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
