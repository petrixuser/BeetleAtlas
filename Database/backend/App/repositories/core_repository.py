from datetime import date
import json
from typing import Optional

from sqlalchemy import text

from Database.Backend.App.core.db import get_connection


def ping_db() -> None:
    with get_connection() as conn:
        conn.execute(text("SELECT 1"))


def fetch_stats_overview_rows():
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
        return conn.execute(sql).mappings().all()


def fetch_species(limit: int, offset: int, order_by_sql: str):
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
        ORDER BY {order_by_sql}
        LIMIT :limit OFFSET :offset
        """
    )
    count_sql = text("SELECT COUNT(*) AS total FROM beetle_species")

    with get_connection() as conn:
        rows = conn.execute(sql, {"limit": limit, "offset": offset}).mappings().all()
        total = conn.execute(count_sql).scalar_one()

    return rows, int(total)


def fetch_observations(
    beetle_id: Optional[int],
    year: Optional[int],
    has_image: Optional[bool],
    limit: int,
    offset: int,
    order_by_sql: str,
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
        """
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
        ORDER BY {order_by_sql}
        LIMIT :limit OFFSET :offset
        """
    )

    count_sql = text(
        """
        SELECT COUNT(*) AS total
        FROM observation o
        JOIN beetle_species bs ON bs.beetle_id = o.beetle_id
        {where_sql}
        """
    )

    with get_connection() as conn:
        rows = conn.execute(sql, params).mappings().all()
        count_params = {k: v for k, v in params.items() if k not in {"limit", "offset"}}
        total = conn.execute(count_sql, count_params).scalar_one()

    return rows, int(total)


def fetch_climate_by_location(
    location_id: int,
    from_date: Optional[date],
    to_date: Optional[date],
    limit: int,
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
        """
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

    return rows


def fetch_quality_report_rows():
    totals_sql = text(
        """
        SELECT
            (SELECT COUNT(*) FROM observation) AS observation_count,
            (SELECT COUNT(*) FROM location) AS location_count,
            (SELECT COUNT(*) FROM climate_snapshot) AS climate_snapshot_count
        """
    )

    observation_nulls_sql = text(
        """
        SELECT
            SUM(CASE WHEN o.event_date IS NULL OR TRIM(o.event_date) = '' THEN 1 ELSE 0 END) AS event_date_missing,
            SUM(CASE WHEN o.event_date_parsed IS NULL THEN 1 ELSE 0 END) AS event_date_parsed_missing,
            SUM(CASE WHEN o.basis_of_record IS NULL OR TRIM(o.basis_of_record) = '' THEN 1 ELSE 0 END) AS basis_of_record_missing,
            SUM(CASE WHEN o.taxon_id IS NULL THEN 1 ELSE 0 END) AS taxon_id_missing,
            SUM(CASE WHEN o.location_id IS NULL THEN 1 ELSE 0 END) AS location_id_missing,
            SUM(CASE WHEN o.image_available IS NULL THEN 1 ELSE 0 END) AS image_available_missing
        FROM observation o
        """
    )

    location_nulls_sql = text(
        """
        SELECT
            SUM(CASE WHEN l.latitude IS NULL THEN 1 ELSE 0 END) AS latitude_missing,
            SUM(CASE WHEN l.longitude IS NULL THEN 1 ELSE 0 END) AS longitude_missing,
            SUM(CASE WHEN l.elevation IS NULL THEN 1 ELSE 0 END) AS elevation_missing,
            SUM(CASE WHEN l.coordinate_uncertainty IS NULL THEN 1 ELSE 0 END) AS coordinate_uncertainty_missing,
            SUM(CASE WHEN l.worldclim_bio01 IS NULL OR l.worldclim_bio01 = -9999 THEN 1 ELSE 0 END) AS worldclim_bio01_missing,
            SUM(CASE WHEN l.worldclim_bio12 IS NULL OR l.worldclim_bio12 = -9999 THEN 1 ELSE 0 END) AS worldclim_bio12_missing,
            SUM(CASE WHEN l.soil_ph IS NULL OR l.soil_ph = -9999 THEN 1 ELSE 0 END) AS soil_ph_missing,
            SUM(CASE WHEN l.soil_organic_carbon IS NULL OR l.soil_organic_carbon = -9999 THEN 1 ELSE 0 END) AS soil_organic_carbon_missing
        FROM location l
        """
    )

    snapshot_nulls_sql = text(
        """
        SELECT
            SUM(CASE WHEN cs.avg_temperature IS NULL THEN 1 ELSE 0 END) AS avg_temperature_missing,
            SUM(CASE WHEN cs.precipitation IS NULL THEN 1 ELSE 0 END) AS precipitation_missing,
            SUM(CASE WHEN cs.soil_moisture IS NULL THEN 1 ELSE 0 END) AS soil_moisture_missing,
            SUM(CASE WHEN cs.ndvi IS NULL THEN 1 ELSE 0 END) AS ndvi_missing,
            SUM(CASE WHEN cs.relative_humidity IS NULL THEN 1 ELSE 0 END) AS relative_humidity_missing,
            SUM(CASE WHEN cs.surface_pressure_hpa IS NULL THEN 1 ELSE 0 END) AS surface_pressure_hpa_missing,
            SUM(CASE WHEN cs.nighttime_lights IS NULL THEN 1 ELSE 0 END) AS nighttime_lights_missing
        FROM climate_snapshot cs
        """
    )

    ee_coverage_sql = text(
        """
        SELECT
            COUNT(*) AS total_observations,
            SUM(
                CASE WHEN EXISTS (
                    SELECT 1
                    FROM climate_snapshot cs
                    WHERE cs.location_id = o.location_id
                      AND cs.snapshot_date <= COALESCE(
                                                    o.event_date_parsed,
                          STR_TO_DATE(LEFT(o.event_date, 10), '%Y-%m-%d'),
                          DATE('9999-12-31')
                      )
                ) THEN 1 ELSE 0 END
            ) AS with_snapshot_match
        FROM observation o
        """
    )

    with get_connection() as conn:
        totals = conn.execute(totals_sql).mappings().one()
        observation_nulls = conn.execute(observation_nulls_sql).mappings().one()
        location_nulls = conn.execute(location_nulls_sql).mappings().one()
        snapshot_nulls = conn.execute(snapshot_nulls_sql).mappings().one()
        ee_coverage = conn.execute(ee_coverage_sql).mappings().one()

    return totals, observation_nulls, location_nulls, snapshot_nulls, ee_coverage


def insert_quality_report_history_snapshot(
    *,
    source_label: Optional[str],
    observation_count: int,
    location_count: int,
    climate_snapshot_count: int,
    observation_null_rates: list,
    location_null_rates: list,
    climate_snapshot_null_rates: list,
    ee_coverage: dict,
) -> int:
    sql = text(
        """
        INSERT INTO quality_report_history (
            generated_at,
            source_label,
            observation_count,
            location_count,
            climate_snapshot_count,
            observation_null_rates_json,
            location_null_rates_json,
            climate_snapshot_null_rates_json,
            ee_coverage_json
        )
        VALUES (
            UTC_TIMESTAMP(),
            :source_label,
            :observation_count,
            :location_count,
            :climate_snapshot_count,
            CAST(:observation_null_rates_json AS JSON),
            CAST(:location_null_rates_json AS JSON),
            CAST(:climate_snapshot_null_rates_json AS JSON),
            CAST(:ee_coverage_json AS JSON)
        )
        """
    )

    params = {
        "source_label": source_label,
        "observation_count": int(observation_count),
        "location_count": int(location_count),
        "climate_snapshot_count": int(climate_snapshot_count),
        "observation_null_rates_json": json.dumps(observation_null_rates),
        "location_null_rates_json": json.dumps(location_null_rates),
        "climate_snapshot_null_rates_json": json.dumps(climate_snapshot_null_rates),
        "ee_coverage_json": json.dumps(ee_coverage),
    }

    with get_connection() as conn:
        result = conn.execute(sql, params)
        conn.commit()
        return int(result.lastrowid)


def fetch_quality_report_history_rows(limit: int, offset: int):
    sql = text(
        """
        SELECT
            quality_report_id,
            generated_at,
            source_label,
            observation_count,
            location_count,
            climate_snapshot_count,
            observation_null_rates_json,
            location_null_rates_json,
            climate_snapshot_null_rates_json,
            ee_coverage_json
        FROM quality_report_history
        ORDER BY quality_report_id DESC
        LIMIT :limit OFFSET :offset
        """
    )

    count_sql = text("SELECT COUNT(*) AS total FROM quality_report_history")

    with get_connection() as conn:
        rows = conn.execute(sql, {"limit": limit, "offset": offset}).mappings().all()
        total = conn.execute(count_sql).scalar_one()

    return rows, int(total)


def fetch_quality_report_history_row(quality_report_id: int):
    sql = text(
        """
        SELECT
            quality_report_id,
            generated_at,
            source_label,
            observation_count,
            location_count,
            climate_snapshot_count,
            observation_null_rates_json,
            location_null_rates_json,
            climate_snapshot_null_rates_json,
            ee_coverage_json
        FROM quality_report_history
        WHERE quality_report_id = :quality_report_id
        LIMIT 1
        """
    )

    with get_connection() as conn:
        row = conn.execute(sql, {"quality_report_id": quality_report_id}).mappings().first()

    return dict(row) if row is not None else None
