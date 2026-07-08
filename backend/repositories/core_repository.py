"""Repository fuer Kernstatistiken und Qualitaetsberichte."""
from datetime import date
import json
from typing import Optional

from sqlalchemy import text

from backend.config.sql.core_repository_sql import (
    CLIMATE_BY_LOCATION_SQL_TEMPLATE,
    INSERT_QUALITY_REPORT_HISTORY_SQL,
    OBSERVATIONS_COUNT_SQL_TEMPLATE,
    QUALITY_EE_COVERAGE_SQL,
    QUALITY_LOCATION_NULLS_SQL,
    QUALITY_OBSERVATION_NULLS_SQL,
    QUALITY_REPORT_HISTORY_BY_ID_SQL,
    QUALITY_REPORT_HISTORY_COUNT_SQL,
    QUALITY_REPORT_HISTORY_LIST_SQL,
    QUALITY_SNAPSHOT_NULLS_SQL,
    QUALITY_TOTALS_SQL,
    SPECIES_COUNT_SQL,
    STATS_OVERVIEW_SQL,
    build_observations_sql,
    build_species_sql,
)
from backend.core.db import get_connection

def ping_db() -> None:
    """Datenbank anpingen, um die Verbindung zu pruefen."""
    with get_connection() as conn:
        conn.execute(text("SELECT 1"))

def fetch_stats_overview_rows():
    """Zeilenzahlen der wichtigsten Anwendungstabellen laden."""
    sql = text(STATS_OVERVIEW_SQL)

    with get_connection() as conn:
        return conn.execute(sql).mappings().all()

def fetch_species(limit: int, offset: int, order_by_sql: str):
    """Seitenweise Kaeferarten mit Sortierung laden."""
    sql = text(build_species_sql(order_by_sql))
    count_sql = text(SPECIES_COUNT_SQL)

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
    """Seitenweise Beobachtungen mit optionalen Filtern und Sortierung laden."""
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

    sql = text(build_observations_sql(where_sql, order_by_sql))

    count_sql = text(OBSERVATIONS_COUNT_SQL_TEMPLATE.format(where_sql=where_sql))

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
    """Klima-Snapshots eines Standorts in einem optionalen Zeitraum laden."""
    filters = ["location_id = :location_id"]
    params = {"location_id": location_id, "limit": limit}

    if from_date is not None:
        filters.append("snapshot_date >= :from_date")
        params["from_date"] = from_date

    if to_date is not None:
        filters.append("snapshot_date <= :to_date")
        params["to_date"] = to_date

    where_sql = "WHERE " + " AND ".join(filters)

    sql = text(CLIMATE_BY_LOCATION_SQL_TEMPLATE.format(where_sql=where_sql))

    with get_connection() as conn:
        rows = conn.execute(sql, params).mappings().all()

    return rows

def fetch_quality_report_rows():
    """Aggregat-Metriken fuer den Qualitaetsbericht laden."""
    totals_sql = text(QUALITY_TOTALS_SQL)

    observation_nulls_sql = text(QUALITY_OBSERVATION_NULLS_SQL)

    location_nulls_sql = text(QUALITY_LOCATION_NULLS_SQL)

    snapshot_nulls_sql = text(QUALITY_SNAPSHOT_NULLS_SQL)

    ee_coverage_sql = text(QUALITY_EE_COVERAGE_SQL)

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
    """Einen Qualitaetsbericht-Snapshot speichern und dessen ID zurueckgeben."""
    sql = text(INSERT_QUALITY_REPORT_HISTORY_SQL)

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
    """Seitenweise Qualitaetsbericht-Historie laden."""
    sql = text(QUALITY_REPORT_HISTORY_LIST_SQL)

    count_sql = text(QUALITY_REPORT_HISTORY_COUNT_SQL)

    with get_connection() as conn:
        rows = conn.execute(sql, {"limit": limit, "offset": offset}).mappings().all()
        total = conn.execute(count_sql).scalar_one()

    return rows, int(total)

def fetch_quality_report_history_row(quality_report_id: int):
    """Einen Qualitaetsbericht-Snapshot anhand der ID laden."""
    sql = text(QUALITY_REPORT_HISTORY_BY_ID_SQL)

    with get_connection() as conn:
        row = conn.execute(sql, {"quality_report_id": quality_report_id}).mappings().first()

    return dict(row) if row is not None else None
