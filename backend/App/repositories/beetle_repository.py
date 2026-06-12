from typing import Any, Dict, Optional, Tuple

from sqlalchemy import text

from backend.App.core.classifications import (
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
from backend.App.core.db import get_connection


def fetch_beetles_list_rows_total(
    *,
    where_sql: str,
    base_where_sql: str,
    order_by_sql: str,
    limit: int,
    offset: int,
    params: Dict[str, Any],
) -> Tuple[list, int]:
    query_sql = f"""
        WITH media_agg AS (
            SELECT
                m.gbif_id,
                COUNT(*) AS media_count,
                MIN(m.license) AS license_sample,
                MIN(m.image_url) AS image_url_sample
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
                ma.image_url_sample,
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
            LEFT JOIN climate_snapshot lc
                ON lc.location_id = l.location_id
               AND lc.snapshot_date = (
                    SELECT MAX(cs2.snapshot_date)
                    FROM climate_snapshot cs2
                    WHERE cs2.location_id = l.location_id
                      AND cs2.snapshot_date <= COALESCE(
                                                    o.event_date_parsed,
                          STR_TO_DATE(LEFT(o.event_date, 10), '%Y-%m-%d'),
                          DATE('9999-12-31')
                      )
               )
            {base_where_sql}
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
                b.image_url_sample,
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
            e.image_url_sample,
            e.country,
            e.region,
            e.city
        FROM enriched e
        {where_sql}
        ORDER BY {order_by_sql}
        LIMIT :limit OFFSET :offset
    """

    sql = text(query_sql)
    count_query_sql = query_sql.replace(f"ORDER BY {order_by_sql}\n        LIMIT :limit OFFSET :offset", "")
    count_sql = text(f"SELECT COUNT(*) AS total FROM ({count_query_sql}) beetles_subquery")

    exec_params = dict(params)
    exec_params["limit"] = limit
    exec_params["offset"] = offset

    with get_connection() as conn:
        rows = conn.execute(sql, exec_params).mappings().all()
        count_params = {k: v for k, v in exec_params.items() if k not in {"limit", "offset"}}
        total = conn.execute(count_sql, count_params).scalar_one()

    return rows, int(total)


def fetch_beetle_detail_row(gbif_id: int) -> Optional[Dict[str, Any]]:
    sql = text(
        f"""
        WITH media_agg AS (
            SELECT
                m.gbif_id,
                COUNT(*) AS media_count,
                MIN(m.license) AS license_sample,
                MIN(m.image_url) AS image_url_sample
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
                ma.image_url_sample,
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
            LEFT JOIN climate_snapshot lc
                ON lc.location_id = l.location_id
               AND lc.snapshot_date = (
                    SELECT MAX(cs2.snapshot_date)
                    FROM climate_snapshot cs2
                    WHERE cs2.location_id = l.location_id
                      AND cs2.snapshot_date <= COALESCE(
                                                    o.event_date_parsed,
                          STR_TO_DATE(LEFT(o.event_date, 10), '%Y-%m-%d'),
                          DATE('9999-12-31')
                      )
               )
            WHERE o.gbif_id = :gbif_id
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
                b.image_url_sample,
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
        SELECT *
        FROM enriched
        LIMIT 1
        """
    )

    with get_connection() as conn:
        row = conn.execute(sql, {"gbif_id": gbif_id}).mappings().first()

    return dict(row) if row is not None else None


def fetch_beetle_media_rows(gbif_id: int, limit: int = 8):
    sql = text(
        """
        SELECT
            m.image_url,
            m.license,
            m.creator,
            m.publisher,
            m.rights_holder
        FROM media m
        WHERE m.gbif_id = :gbif_id
          AND m.image_url IS NOT NULL
          AND TRIM(m.image_url) <> ''
        ORDER BY m.media_id ASC
        LIMIT :limit
        """
    )

    with get_connection() as conn:
        rows = conn.execute(sql, {"gbif_id": gbif_id, "limit": limit}).mappings().all()

    return [dict(row) for row in rows]


def fetch_beetle_media_rows_total(gbif_id: int, limit: int, offset: int):
    sql = text(
        """
        SELECT
            m.media_id,
            m.image_url,
            m.license,
            m.creator,
            m.publisher,
            m.rights_holder,
            m.references
        FROM media m
        WHERE m.gbif_id = :gbif_id
          AND m.image_url IS NOT NULL
          AND TRIM(m.image_url) <> ''
        ORDER BY m.media_id ASC
        LIMIT :limit OFFSET :offset
        """
    )

    count_sql = text(
        """
        SELECT COUNT(*) AS total
        FROM media m
        WHERE m.gbif_id = :gbif_id
          AND m.image_url IS NOT NULL
          AND TRIM(m.image_url) <> ''
        """
    )

    with get_connection() as conn:
        rows = conn.execute(sql, {"gbif_id": gbif_id, "limit": limit, "offset": offset}).mappings().all()
        total = conn.execute(count_sql, {"gbif_id": gbif_id}).scalar_one()

    return [dict(row) for row in rows], int(total)


def fetch_country_detail_rows(country_code: str):
    base_sql = text(
        f"""
        WITH base AS (
            SELECT
                o.beetle_id,
                l.country,
                l.elevation,
                l.landcover_class,
                CASE
                    WHEN l.worldclim_bio01 IS NULL OR l.worldclim_bio01 = -9999 THEN NULL
                    WHEN l.worldclim_bio01 > 80 THEN l.worldclim_bio01 / 10
                    ELSE l.worldclim_bio01
                END AS worldclim_bio01,
                COALESCE(
                    lc.avg_temperature,
                    CASE
                        WHEN l.worldclim_bio01 IS NULL OR l.worldclim_bio01 = -9999 THEN NULL
                        WHEN l.worldclim_bio01 > 80 THEN l.worldclim_bio01 / 10
                        ELSE l.worldclim_bio01
                    END
                ) AS temperature_value,
                COALESCE(lc.precipitation, l.worldclim_bio12) AS precipitation_value
            FROM observation o
            JOIN location l ON l.location_id = o.location_id
            LEFT JOIN climate_snapshot lc
                ON lc.location_id = l.location_id
               AND lc.snapshot_date = (
                    SELECT MAX(cs2.snapshot_date)
                    FROM climate_snapshot cs2
                    WHERE cs2.location_id = l.location_id
                      AND cs2.snapshot_date <= COALESCE(
                                                    o.event_date_parsed,
                          STR_TO_DATE(LEFT(o.event_date, 10), '%Y-%m-%d'),
                          DATE('9999-12-31')
                      )
               )
            WHERE UPPER(COALESCE(l.country, '')) = :country_code
        ),
        enriched AS (
            SELECT
                b.beetle_id,
                b.country,
                b.elevation,
                {CLIMATE_CASE_SQL} AS climate,
                {VEGETATION_CASE_SQL} AS vegetation
            FROM base b
        )
        SELECT
            COUNT(DISTINCT beetle_id) AS species_count,
            MIN(elevation) AS min_elevation,
            MAX(elevation) AS max_elevation,
            MIN(country) AS country_name
        FROM enriched
        """
    )

    top_climates_sql = text(
        f"""
        WITH base AS (
            SELECT
                l.country,
                CASE
                    WHEN l.worldclim_bio01 IS NULL OR l.worldclim_bio01 = -9999 THEN NULL
                    WHEN l.worldclim_bio01 > 80 THEN l.worldclim_bio01 / 10
                    ELSE l.worldclim_bio01
                END AS worldclim_bio01,
                COALESCE(
                    lc.avg_temperature,
                    CASE
                        WHEN l.worldclim_bio01 IS NULL OR l.worldclim_bio01 = -9999 THEN NULL
                        WHEN l.worldclim_bio01 > 80 THEN l.worldclim_bio01 / 10
                        ELSE l.worldclim_bio01
                    END
                ) AS temperature_value,
                COALESCE(lc.precipitation, l.worldclim_bio12) AS precipitation_value
            FROM observation o
            JOIN location l ON l.location_id = o.location_id
            LEFT JOIN climate_snapshot lc
                ON lc.location_id = l.location_id
               AND lc.snapshot_date = (
                    SELECT MAX(cs2.snapshot_date)
                    FROM climate_snapshot cs2
                    WHERE cs2.location_id = l.location_id
                      AND cs2.snapshot_date <= COALESCE(
                                                    o.event_date_parsed,
                          STR_TO_DATE(LEFT(o.event_date, 10), '%Y-%m-%d'),
                          DATE('9999-12-31')
                      )
               )
            WHERE UPPER(COALESCE(l.country, '')) = :country_code
        ),
        enriched AS (
            SELECT {CLIMATE_CASE_SQL} AS climate FROM base b
        )
        SELECT climate, COUNT(*) AS cnt
        FROM enriched
        GROUP BY climate
        ORDER BY cnt DESC, climate ASC
        LIMIT 2
        """
    )

    top_vegetation_sql = text(
        f"""
        WITH base AS (
            SELECT l.country, l.landcover_class
            FROM observation o
            JOIN location l ON l.location_id = o.location_id
            WHERE UPPER(COALESCE(l.country, '')) = :country_code
        ),
        enriched AS (
            SELECT {VEGETATION_CASE_SQL} AS vegetation FROM base b
        )
        SELECT vegetation, COUNT(*) AS cnt
        FROM enriched
        GROUP BY vegetation
        ORDER BY cnt DESC, vegetation ASC
        LIMIT 2
        """
    )

    params = {"country_code": country_code}
    with get_connection() as conn:
        overview = conn.execute(base_sql, params).mappings().first()
        climates = conn.execute(top_climates_sql, params).mappings().all()
        vegetations = conn.execute(top_vegetation_sql, params).mappings().all()

    return overview, climates, vegetations
