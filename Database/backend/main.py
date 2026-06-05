from datetime import date
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Query
from sqlalchemy import text

from classifications import (
    BASIS_OF_RECORD_CASE_SQL,
    CLIMATE_CASE_SQL,
    COORDINATE_UNCERTAINTY_BAND_CASE_SQL,
    ELEVATION_GROUP_CASE_SQL,
    EVENT_DATE_QUALITY_CASE_SQL,
    HUMAN_MODIFICATION_BAND_CASE_SQL,
    HUMIDITY_BAND_CASE_SQL,
    LANDCOVER_GROUP_CASE_SQL,
    LICENSE_CLASS_CASE_SQL,
    LIGHT_POLLUTION_BAND_CASE_SQL,
    MEDIA_COVERAGE_CASE_SQL,
    NDVI_BAND_CASE_SQL,
    PRECIPITATION_BAND_CASE_SQL,
    PRESSURE_BAND_CASE_SQL,
    SLOPE_BAND_CASE_SQL,
    SOIL_CARBON_BAND_CASE_SQL,
    SOIL_CASE_SQL,
    SOIL_MOISTURE_BAND_CASE_SQL,
    SOIL_PH_BAND_CASE_SQL,
    TAXON_RESOLUTION_CASE_SQL,
    TEMPERATURE_BAND_CASE_SQL,
    VEGETATION_CASE_SQL,
    WATER_DISTANCE_BAND_CASE_SQL,
    WORLDCLIM_PRECIP_BAND_CASE_SQL,
    WORLCLIM_TEMP_BAND_CASE_SQL,
)
from db import get_connection
from field_mappings import FIELD_MAPPINGS
from payloads import FILTER_OPTIONS, to_beetle_payload


app = FastAPI(title="Beetle API", version="1.0.0")


@app.get("/health")
def healthcheck():
    with get_connection() as conn:
        conn.execute(text("SELECT 1"))
    return {"status": "ok"}


@app.get("/stats/overview")
def stats_overview():
    sql = text(
        """
        SELECT 'beetle_species' AS table_name, COUNT(*) AS rows_count FROM beetle_species
        UNION ALL SELECT 'location', COUNT(*) FROM location
        UNION ALL SELECT 'observation', COUNT(*) FROM observation
        UNION ALL SELECT 'media', COUNT(*) FROM media
        UNION ALL SELECT 'climate_snapshot', COUNT(*) FROM climate_snapshot
        """
    )

    with get_connection() as conn:
        rows = conn.execute(sql).mappings().all()

    return {"tables": rows}


@app.get("/species")
def list_species(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
):
    sql = text(
        """
        SELECT
            beetle_id,
            taxon_id,
            family,
            genus,
            specific_epithet,
            scientific_name
        FROM beetle_species
        ORDER BY beetle_id
        LIMIT :limit OFFSET :offset
        """
    )

    with get_connection() as conn:
        rows = conn.execute(sql, {"limit": limit, "offset": offset}).mappings().all()

    return {"items": rows, "limit": limit, "offset": offset}


@app.get("/api/filters")
def list_frontend_filters():
    return FILTER_OPTIONS


@app.get("/api/field-mappings")
def list_field_mappings():
    return {"tables": FIELD_MAPPINGS}


@app.get("/api/beetles")
def list_beetles(
    q: Optional[str] = Query(None, max_length=200),
    climate: Optional[str] = Query(None),
    vegetation: Optional[str] = Query(None),
    elevation: Optional[str] = Query(None, pattern="^(low|mid|high|veryHigh)$"),
    temperature_band: Optional[str] = Query(None),
    precipitation_band: Optional[str] = Query(None),
    soil_moisture_band: Optional[str] = Query(None),
    ndvi_band: Optional[str] = Query(None),
    humidity_band: Optional[str] = Query(None),
    pressure_band: Optional[str] = Query(None),
    light_pollution_band: Optional[str] = Query(None),
    slope_band: Optional[str] = Query(None),
    water_distance_band: Optional[str] = Query(None),
    human_impact_band: Optional[str] = Query(None),
    landcover_group: Optional[str] = Query(None),
    coordinate_uncertainty_band: Optional[str] = Query(None),
    soil_ph_band: Optional[str] = Query(None),
    soil_carbon_band: Optional[str] = Query(None),
    worldclim_temp_band: Optional[str] = Query(None),
    worldclim_precip_band: Optional[str] = Query(None),
    event_date_quality: Optional[str] = Query(None),
    basis_of_record_class: Optional[str] = Query(None),
    taxon_resolution: Optional[str] = Query(None),
    media_coverage: Optional[str] = Query(None),
    license_class: Optional[str] = Query(None),
    limit: Optional[int] = Query(10000, ge=1, le=50000),
    offset: int = Query(0, ge=0),
):
    filters: List[str] = []
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

    limit_sql = ""
    if limit is not None:
        params["limit"] = limit
        limit_sql = "LIMIT :limit OFFSET :offset"

    where_sql = ""
    if filters:
        where_sql = "WHERE " + " AND ".join(filters)

    sql = text(
        f"""
        WITH latest_climate AS (
            SELECT
                cs.location_id,
                cs.avg_temperature,
                cs.precipitation,
                cs.soil_moisture,
                cs.ndvi,
                cs.relative_humidity,
                cs.surface_pressure_hpa,
                cs.nighttime_lights,
                ROW_NUMBER() OVER (
                    PARTITION BY cs.location_id
                    ORDER BY cs.snapshot_date DESC
                ) AS rn
            FROM climate_snapshot cs
        ),
        media_agg AS (
            SELECT
                m.gbif_id,
                COUNT(*) AS media_count,
                MIN(m.license) AS license_sample
            FROM media m
            GROUP BY m.gbif_id
        ),
        base AS (
            SELECT
                o.gbif_id,
                o.event_date,
                o.basis_of_record,
                o.dataset_name,
                o.institution_code,
                o.image_available,
                o.taxon_id,
                bs.scientific_name,
                bs.family,
                bs.genus,
                bs.specific_epithet,
                l.latitude,
                l.longitude,
                l.city,
                l.region,
                l.country,
                l.verbatim_locality,
                l.coordinate_uncertainty,
                l.elevation,
                l.landcover_class,
                l.biome_id,
                l.ecoregion_id,
                l.distance_to_water_m,
                l.human_modification,
                l.slope,
                CASE
                    WHEN l.soil_ph IS NULL OR l.soil_ph = -9999 THEN NULL
                    WHEN l.soil_ph > 14 THEN l.soil_ph / 10
                    ELSE l.soil_ph
                END AS soil_ph,
                CASE
                    WHEN l.soil_organic_carbon IS NULL OR l.soil_organic_carbon = -9999 THEN NULL
                    WHEN l.soil_organic_carbon > 60 THEN l.soil_organic_carbon / 5
                    ELSE l.soil_organic_carbon
                END AS soil_organic_carbon,
                CASE
                    WHEN l.worldclim_bio01 IS NULL OR l.worldclim_bio01 = -9999 THEN NULL
                    WHEN l.worldclim_bio01 > 80 THEN l.worldclim_bio01 / 10
                    ELSE l.worldclim_bio01
                END AS worldclim_bio01,
                l.worldclim_bio12,
                ma.media_count,
                ma.license_sample,
                COALESCE(
                    lc.avg_temperature,
                    CASE
                        WHEN l.worldclim_bio01 IS NULL OR l.worldclim_bio01 = -9999 THEN NULL
                        WHEN l.worldclim_bio01 > 80 THEN l.worldclim_bio01 / 10
                        ELSE l.worldclim_bio01
                    END
                ) AS temperature_value,
                COALESCE(lc.precipitation, l.worldclim_bio12) AS precipitation_value,
                lc.soil_moisture AS soil_moisture_value,
                lc.ndvi AS ndvi_value,
                lc.relative_humidity AS relative_humidity_value,
                lc.surface_pressure_hpa AS surface_pressure_hpa_value,
                lc.nighttime_lights AS nighttime_lights_value
            FROM observation o
            JOIN beetle_species bs ON bs.beetle_id = o.beetle_id
            JOIN location l ON l.location_id = o.location_id
            LEFT JOIN media_agg ma ON ma.gbif_id = o.gbif_id
            LEFT JOIN latest_climate lc
                ON lc.location_id = l.location_id
               AND lc.rn = 1
        ),
        enriched AS (
            SELECT
                b.gbif_id,
                b.event_date AS observedAt,
                b.scientific_name AS name,
                b.family,
                b.latitude AS lat,
                b.longitude AS lng,
                COALESCE(
                    NULLIF(b.verbatim_locality, ''),
                    NULLIF(CONCAT_WS(', ', b.city, b.region, b.country), ''),
                    NULLIF(CONCAT_WS(', ', b.region, b.country), ''),
                    b.country,
                    'Unbekannt'
                ) AS location,
                {CLIMATE_CASE_SQL} AS climate,
                {VEGETATION_CASE_SQL} AS vegetation,
                {ELEVATION_GROUP_CASE_SQL} AS elevationGroup,
                {TEMPERATURE_BAND_CASE_SQL} AS temperature_band,
                {PRECIPITATION_BAND_CASE_SQL} AS precipitation_band,
                {SOIL_MOISTURE_BAND_CASE_SQL} AS soil_moisture_band,
                {NDVI_BAND_CASE_SQL} AS ndvi_band,
                {HUMIDITY_BAND_CASE_SQL} AS humidity_band,
                {PRESSURE_BAND_CASE_SQL} AS pressure_band,
                {LIGHT_POLLUTION_BAND_CASE_SQL} AS light_pollution_band,
                {SLOPE_BAND_CASE_SQL} AS slope_band,
                {WATER_DISTANCE_BAND_CASE_SQL} AS water_distance_band,
                {HUMAN_MODIFICATION_BAND_CASE_SQL} AS human_modification_band,
                {LANDCOVER_GROUP_CASE_SQL} AS landcover_group,
                {COORDINATE_UNCERTAINTY_BAND_CASE_SQL} AS coordinate_uncertainty_band,
                {SOIL_PH_BAND_CASE_SQL} AS soil_ph_band,
                {SOIL_CARBON_BAND_CASE_SQL} AS soil_carbon_band,
                {WORLCLIM_TEMP_BAND_CASE_SQL} AS worldclim_temp_band,
                {WORLDCLIM_PRECIP_BAND_CASE_SQL} AS worldclim_precip_band,
                {EVENT_DATE_QUALITY_CASE_SQL} AS event_date_quality,
                {BASIS_OF_RECORD_CASE_SQL} AS basis_of_record_class,
                {TAXON_RESOLUTION_CASE_SQL} AS taxon_resolution,
                {MEDIA_COVERAGE_CASE_SQL} AS media_coverage,
                {LICENSE_CLASS_CASE_SQL} AS license_class,
                b.coordinate_uncertainty,
                b.worldclim_bio01,
                b.worldclim_bio12,
                b.soil_ph,
                b.soil_organic_carbon,
                b.basis_of_record,
                b.dataset_name,
                b.institution_code,
                b.image_available,
                b.taxon_id,
                b.genus,
                b.specific_epithet,
                b.media_count,
                b.license_sample,
                b.country,
                b.region,
                b.city,
                b.elevation,
                b.temperature_value AS temperature,
                b.precipitation_value AS precipitation,
                b.soil_moisture_value AS soil_moisture,
                b.ndvi_value AS ndvi,
                b.relative_humidity_value AS relative_humidity,
                b.surface_pressure_hpa_value AS surface_pressure_hpa,
                b.nighttime_lights_value AS nighttime_lights,
                b.slope,
                b.distance_to_water_m,
                b.human_modification,
                b.landcover_class,
                b.ecoregion_id,
                b.biome_id,
                {SOIL_CASE_SQL} AS soil
            FROM base b
        )
        SELECT
            e.gbif_id,
            e.observedAt,
            e.name,
            e.family,
            e.lat,
            e.lng,
            e.location,
            e.climate,
            e.vegetation,
            e.elevationGroup,
            e.elevation,
            e.temperature,
            e.soil,
            e.temperature_band,
            e.precipitation_band,
            e.soil_moisture_band,
            e.ndvi_band,
            e.humidity_band,
            e.pressure_band,
            e.light_pollution_band,
            e.slope_band,
            e.water_distance_band,
            e.human_modification_band,
            e.landcover_group,
            e.coordinate_uncertainty_band,
            e.soil_ph_band,
            e.soil_carbon_band,
            e.worldclim_temp_band,
            e.worldclim_precip_band,
            e.event_date_quality,
            e.basis_of_record_class,
            e.taxon_resolution,
            e.media_coverage,
            e.license_class,
            e.precipitation,
            e.soil_moisture,
            e.ndvi,
            e.relative_humidity,
            e.surface_pressure_hpa,
            e.nighttime_lights,
            e.slope,
            e.distance_to_water_m,
            e.human_modification,
            e.landcover_class,
            e.ecoregion_id,
            e.biome_id,
            e.coordinate_uncertainty,
            e.worldclim_bio01,
            e.worldclim_bio12,
            e.soil_ph,
            e.soil_organic_carbon,
            e.basis_of_record,
            e.dataset_name,
            e.institution_code,
            e.image_available,
            e.taxon_id,
            e.genus,
            e.specific_epithet,
            e.media_count,
            e.license_sample,
            e.country,
            e.region,
            e.city
        FROM enriched e
        {where_sql}
        ORDER BY e.gbif_id
        {limit_sql}
        """
    )

    with get_connection() as conn:
        rows = conn.execute(sql, params).mappings().all()

    return [to_beetle_payload(dict(row)) for row in rows]


@app.get("/observations")
def list_observations(
    beetle_id: Optional[int] = None,
    year: Optional[int] = Query(None, ge=1800, le=2100),
    has_image: Optional[bool] = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
):
    filters = []
    params = {"limit": limit, "offset": offset}

    if beetle_id is not None:
        filters.append("o.beetle_id = :beetle_id")
        params["beetle_id"] = beetle_id

    if year is not None:
        filters.append("LEFT(o.event_date, 4) = :year")
        params["year"] = str(year)

    if has_image is not None:
        filters.append("o.image_available = :has_image")
        params["has_image"] = 1 if has_image else 0

    where_sql = ""
    if filters:
        where_sql = "WHERE " + " AND ".join(filters)

    sql = text(
        f"""
        SELECT
            o.gbif_id,
            o.beetle_id,
            o.location_id,
            o.event_date,
            o.dataset_name,
            o.image_available,
            bs.scientific_name
        FROM observation o
        JOIN beetle_species bs ON bs.beetle_id = o.beetle_id
        {where_sql}
        ORDER BY o.gbif_id
        LIMIT :limit OFFSET :offset
        """
    )

    with get_connection() as conn:
        rows = conn.execute(sql, params).mappings().all()

    return {"items": rows, "limit": limit, "offset": offset}


@app.get("/climate/location/{location_id}")
def climate_by_location(
    location_id: int,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    limit: int = Query(500, ge=1, le=5000),
):
    filters = ["location_id = :location_id"]
    params = {"location_id": location_id, "limit": limit}

    if from_date is not None:
        filters.append("snapshot_date >= :from_date")
        params["from_date"] = from_date

    if to_date is not None:
        filters.append("snapshot_date <= :to_date")
        params["to_date"] = to_date

    where_sql = "WHERE " + " AND ".join(filters)

    sql = text(
        f"""
        SELECT
            location_id,
            snapshot_date,
            avg_temperature,
            precipitation,
            soil_moisture,
            ndvi,
            relative_humidity,
            surface_pressure_hpa,
            nighttime_lights
        FROM climate_snapshot
        {where_sql}
        ORDER BY snapshot_date
        LIMIT :limit
        """
    )

    with get_connection() as conn:
        rows = conn.execute(sql, params).mappings().all()

    return {"location_id": location_id, "items": rows}
