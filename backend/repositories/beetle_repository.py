from typing import Any, Dict, Optional, Tuple

from sqlalchemy import text

from backend.config.classifications_sql import (
    CLIMATE_CASE_SQL,
    VEGETATION_CASE_SQL,
)
from backend.config.beetle_repository_sql import (
    full_enriched_cte_sql,
    full_result_projection_sql,
    lean_enriched_cte_sql,
    latest_snapshot_join_sql,
    normalized_worldclim_bio01_sql,
)
from backend.core.db import get_connection


def _execute_paginated_queries(sql, count_sql, params: Dict[str, Any], limit: int, offset: int) -> Tuple[list, int]:
    exec_params = dict(params)
    exec_params["limit"] = limit
    exec_params["offset"] = offset

    with get_connection() as conn:
        rows = conn.execute(sql, exec_params).mappings().all()
        count_params = {k: v for k, v in exec_params.items() if k not in {"limit", "offset"}}
        total = conn.execute(count_sql, count_params).scalar_one()

    return rows, int(total)




def fetch_beetles_list_rows_total(
    *,
    where_sql: str,
    base_where_sql: str,
    order_by_sql: str,
    limit: int,
    offset: int,
    params: Dict[str, Any],
) -> Tuple[list, int]:
    """Fetch paginated beetle rows (full payload) and total count."""
    query_sql = f"""
        {full_enriched_cte_sql(base_where_sql)}
        SELECT
            {full_result_projection_sql("e")}
        FROM enriched e
        {where_sql}
        ORDER BY {order_by_sql}
        LIMIT :limit OFFSET :offset
    """

    sql = text(query_sql)
    count_query_sql = query_sql.replace(f"ORDER BY {order_by_sql}\n        LIMIT :limit OFFSET :offset", "")
    count_sql = text(f"SELECT COUNT(*) AS total FROM ({count_query_sql}) beetles_subquery")

    return _execute_paginated_queries(sql, count_sql, params, limit, offset)


def fetch_beetles_list_lean(
    *,
    where_sql: str,
    base_where_sql: str,
    order_by_sql: str,
    limit: int,
    offset: int,
    params: Dict[str, Any],
) -> Tuple[list, int]:
    """Fetch paginated beetle rows (lean payload) and total count."""
    cte_sql = lean_enriched_cte_sql(base_where_sql)

    sql = text(
        f"""
        {cte_sql}
        SELECT
            e.*,
            (
                SELECT MIN(m.image_url)
                FROM media m
                WHERE m.gbif_id = e.gbif_id
                  AND m.image_url IS NOT NULL
                  AND TRIM(m.image_url) <> ''
            ) AS image_url_sample,
            (
                SELECT COUNT(*) FROM media m WHERE m.gbif_id = e.gbif_id
            ) AS media_count
        FROM enriched e
        {where_sql}
        ORDER BY {order_by_sql}
        LIMIT :limit OFFSET :offset
        """
    )

    count_sql = text(
        f"""
        {cte_sql}
        SELECT COUNT(*) AS total
        FROM enriched e
        {where_sql}
        """
    )

    return _execute_paginated_queries(sql, count_sql, params, limit, offset)

def fetch_beetle_detail_row(gbif_id: int) -> Optional[Dict[str, Any]]:
    """Fetch one detailed beetle observation row by GBIF ID."""
    cte_sql = full_enriched_cte_sql("WHERE o.gbif_id = :gbif_id")
    sql = text(
        f"""
        {cte_sql}
        SELECT *
        FROM enriched
        LIMIT 1
        """
    )

    with get_connection() as conn:
        row = conn.execute(sql, {"gbif_id": gbif_id}).mappings().first()

    return dict(row) if row is not None else None

def fetch_beetle_media_rows(gbif_id: int, limit: int = 8):
    """Fetch a limited list of media entries for one beetle observation."""
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
    """Fetch paginated media entries and total count for one beetle observation."""
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
    """Fetch country-level overview and top climate/vegetation buckets."""
    base_sql = text(
        f"""
        WITH base AS (
            SELECT
                o.beetle_id,
                l.country,
                l.elevation,
                l.landcover_class,
                {normalized_worldclim_bio01_sql("l")} AS worldclim_bio01,
                COALESCE(
                    lc.avg_temperature,
                    {normalized_worldclim_bio01_sql("l")}
                ) AS temperature_value,
                COALESCE(lc.precipitation, l.worldclim_bio12) AS precipitation_value
            FROM observation o
            JOIN location l ON l.location_id = o.location_id
            {latest_snapshot_join_sql("l", "o")}
            WHERE UPPER(COALESCE(l.country, '')) = :country_code
        ),
        enriched AS (
            SELECT
                b.beetle_id,
                b.country,
                b.elevation,
                b.temperature_value,
                b.precipitation_value,
                {CLIMATE_CASE_SQL} AS climate,
                {VEGETATION_CASE_SQL} AS vegetation
            FROM base b
        )
        SELECT
            COUNT(DISTINCT beetle_id) AS species_count,
            COUNT(*) AS observation_count,
            MIN(elevation) AS min_elevation,
            AVG(elevation) AS avg_elevation,
            MAX(elevation) AS max_elevation,
            AVG(temperature_value) AS avg_temperature,
            AVG(precipitation_value) AS avg_precipitation,
            MIN(country) AS country_name
        FROM enriched
        """
    )

    top_climates_sql = text(
        f"""
        WITH base AS (
            SELECT
                l.country,
                {normalized_worldclim_bio01_sql("l")} AS worldclim_bio01,
                COALESCE(
                    lc.avg_temperature,
                    {normalized_worldclim_bio01_sql("l")}
                ) AS temperature_value,
                COALESCE(lc.precipitation, l.worldclim_bio12) AS precipitation_value
            FROM observation o
            JOIN location l ON l.location_id = o.location_id
            {latest_snapshot_join_sql("l", "o")}
            WHERE UPPER(COALESCE(l.country, '')) = :country_code
        ),
        enriched AS (
            SELECT {CLIMATE_CASE_SQL} AS climate FROM base b
        )
        SELECT climate, COUNT(*) AS cnt
        FROM enriched
        GROUP BY climate
        ORDER BY cnt DESC, climate ASC
        LIMIT 3
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
        LIMIT 3
        """
    )

    # Top-3 Kaeferarten des Landes: haeufigste Arten nach Fundzahl.
    top_beetles_sql = text(
        """
        SELECT
            bs.scientific_name AS name,
            bs.family AS family,
            COUNT(*) AS cnt
        FROM observation o
        JOIN location l ON l.location_id = o.location_id
        JOIN beetle_species bs ON bs.beetle_id = o.beetle_id
        WHERE UPPER(COALESCE(l.country, '')) = :country_code
        GROUP BY o.beetle_id, bs.scientific_name, bs.family
        ORDER BY cnt DESC, name ASC
        LIMIT 3
        """
    )

    params = {"country_code": country_code}
    with get_connection() as conn:
        overview = conn.execute(base_sql, params).mappings().first()
        climates = conn.execute(top_climates_sql, params).mappings().all()
        vegetations = conn.execute(top_vegetation_sql, params).mappings().all()
        top_beetles = conn.execute(top_beetles_sql, params).mappings().all()

    return overview, climates, vegetations, top_beetles
