from typing import Any, Dict, Optional, Tuple

from sqlalchemy import text

from backend.config.beetle_repository_sql import (
    compact_rows_select_sql,
    country_overview_sql,
    country_top_beetles_sql,
    country_top_climates_sql,
    country_top_koppen_sql,
    country_top_vegetation_sql,
    country_top_vegetation_zone_sql,
    full_enriched_cte_sql,
    full_result_projection_sql,
    lean_enriched_cte_sql,
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
    cte_sql = full_enriched_cte_sql(base_where_sql)
    select_from_sql = f"""
        SELECT
            {full_result_projection_sql("e")}
        FROM enriched e
        {where_sql}
    """

    sql = text(
        f"""
        {cte_sql}
        {select_from_sql}
        ORDER BY {order_by_sql}
        LIMIT :limit OFFSET :offset
        """
    )
    count_sql = text(
        f"""
        {cte_sql}
        SELECT COUNT(*) AS total
        FROM (
            {select_from_sql}
        ) beetles_subquery
        """
    )

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


def fetch_beetles_list_compact_rows(
    *,
    where_sql: str,
    order_by_sql: str,
    limit: int,
    offset: int,
    params: Dict[str, Any],
) -> list:
    """Fetch compact paginated list rows from precomputed beetle_list_read."""
    sql = text(compact_rows_select_sql(where_sql, order_by_sql))

    exec_params = dict(params)
    exec_params["limit"] = limit
    exec_params["offset"] = offset

    with get_connection() as conn:
        return conn.execute(sql, exec_params).mappings().all()


def fetch_beetles_list_compact_total(
    *,
    where_sql: str,
    params: Dict[str, Any],
) -> int:
    """Fetch total count for compact list rows from precomputed read models."""
    with get_connection() as conn:
        if not where_sql.strip():
            total = conn.execute(
                text(
                    """
                    SELECT metric_value
                    FROM beetle_list_meta_read
                    WHERE metric_key = 'total_rows'
                    LIMIT 1
                    """
                )
            ).scalar_one_or_none()
            if total is None:
                total = conn.execute(text("SELECT COUNT(*) FROM beetle_list_read")).scalar_one()
        else:
            total = conn.execute(
                text(
                    f"""
                    SELECT COUNT(*) AS total
                    FROM beetle_list_read e
                    {where_sql}
                    """
                ),
                params,
            ).scalar_one()
    return int(total)


def fetch_beetles_list_compact_total_precomputed(dim_name: str, dim_value: str) -> Optional[int]:
    """Fetch precomputed compact total for one filter dimension/value pair."""
    with get_connection() as conn:
        value = conn.execute(
            text(
                """
                SELECT cnt
                FROM beetle_list_filter_count_read
                WHERE dim_name = :dim_name
                  AND dim_value = :dim_value
                LIMIT 1
                """
            ),
            {"dim_name": dim_name, "dim_value": dim_value},
        ).scalar_one_or_none()
    return int(value) if value is not None else None


def fetch_beetles_list_compact(
    *,
    where_sql: str,
    order_by_sql: str,
    limit: int,
    offset: int,
    params: Dict[str, Any],
) -> Tuple[list, int]:
    """Compatibility wrapper: fetch compact rows and total."""
    rows = fetch_beetles_list_compact_rows(
        where_sql=where_sql,
        order_by_sql=order_by_sql,
        limit=limit,
        offset=offset,
        params=params,
    )
    total = fetch_beetles_list_compact_total(where_sql=where_sql, params=params)
    return rows, total

def fetch_beetle_detail_row(gbif_id: int) -> Optional[Dict[str, Any]]:
    """Fetch one detailed beetle observation row by GBIF ID."""
    return fetch_beetle_detail_row_by_entity(f"occ-{gbif_id}")


def fetch_beetle_detail_row_by_entity(entity_id: str) -> Optional[Dict[str, Any]]:
    """Fetch one detailed beetle row by API entity id (occ-* or rec-*)."""
    params: Dict[str, Any] = {"entity_id": entity_id}
    base_where_sql = ""
    media_where_sql = ""
    # Fast path for GBIF observations (occ-<gbif_id>): push the id into the
    # observation branch AND the media_agg CTE so we enrich a single row instead
    # of scanning all 417k observations and aggregating the whole media table.
    # gbif_id is observation's PRIMARY KEY and media has idx_media_gbif_id, so
    # this turns a ~2s detail lookup into an index lookup. Manual records (rec-*)
    # are few, so their branch stays unfiltered (still cheap).
    if entity_id.startswith("occ-"):
        suffix = entity_id[4:]
        if suffix.isdigit():
            base_where_sql = "WHERE o.gbif_id = :detail_gbif_id"
            media_where_sql = "WHERE m.gbif_id = :detail_gbif_id"
            params["detail_gbif_id"] = int(suffix)

    cte_sql = full_enriched_cte_sql(base_where_sql, media_where_sql)
    sql = text(
        f"""
        {cte_sql}
        SELECT *
        FROM enriched e
        WHERE e.entity_id = :entity_id
        LIMIT 1
        """
    )

    with get_connection() as conn:
        row = conn.execute(sql, params).mappings().first()

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
    params = {"country_code": country_code}
    with get_connection() as conn:
        overview = conn.execute(text(country_overview_sql()), params).mappings().first()
        climates = conn.execute(text(country_top_climates_sql()), params).mappings().all()
        vegetations = conn.execute(text(country_top_vegetation_sql()), params).mappings().all()
        koppen = conn.execute(text(country_top_koppen_sql()), params).mappings().all()
        vegetation_zones = conn.execute(text(country_top_vegetation_zone_sql()), params).mappings().all()
        top_beetles = conn.execute(text(country_top_beetles_sql()), params).mappings().all()

    return overview, climates, vegetations, koppen, vegetation_zones, top_beetles


def fetch_environment_ranges() -> Dict[str, Optional[float]]:
    """Fetch global min/max values for environmental metrics used in detail quicklook bars."""
    cte_sql = full_enriched_cte_sql("")
    sql = text(
        f"""
        {cte_sql}
        SELECT
            MIN(e.elevation) AS min_elevation,
            MAX(e.elevation) AS max_elevation,
            MIN(e.temperature) AS min_temperature,
            MAX(e.temperature) AS max_temperature,
            MIN(e.worldclim_bio01) AS min_worldclim_bio01,
            MAX(e.worldclim_bio01) AS max_worldclim_bio01,
            MIN(e.precipitation) AS min_precipitation,
            MAX(e.precipitation) AS max_precipitation,
            MIN(e.worldclim_bio12) AS min_worldclim_bio12,
            MAX(e.worldclim_bio12) AS max_worldclim_bio12,
            MIN(e.soil_moisture) AS min_soil_moisture,
            MAX(e.soil_moisture) AS max_soil_moisture,
            MIN(e.ndvi) AS min_ndvi,
            MAX(e.ndvi) AS max_ndvi,
            MIN(e.relative_humidity) AS min_relative_humidity,
            MAX(e.relative_humidity) AS max_relative_humidity,
            MIN(e.surface_pressure_hpa) AS min_surface_pressure_hpa,
            MAX(e.surface_pressure_hpa) AS max_surface_pressure_hpa,
            MIN(e.nighttime_lights) AS min_nighttime_lights,
            MAX(e.nighttime_lights) AS max_nighttime_lights,
            MIN(e.slope) AS min_slope,
            MAX(e.slope) AS max_slope,
            MIN(e.distance_to_water_m) AS min_distance_to_water_m,
            MAX(e.distance_to_water_m) AS max_distance_to_water_m,
            MIN(e.human_modification) AS min_human_modification,
            MAX(e.human_modification) AS max_human_modification
        FROM enriched e
        """
    )

    with get_connection() as conn:
        row = conn.execute(sql).mappings().first()

    return dict(row) if row is not None else {}
