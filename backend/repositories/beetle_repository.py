"""Lese-Repository fuer Kaefer-Listen und -Details (Read-Pfad)."""
from typing import Any, Dict, Optional, Tuple

from sqlalchemy import text

from backend.config.environment_metrics import ENVIRONMENT_METRICS
from backend.config.sql.beetle_repository_sql import (
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
    """Fuehrt eine seitenweise Abfrage samt Gesamtzahl aus und liefert (Zeilen, total)."""
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
    """Seitenweise Kaefer-Zeilen (vollstaendiges Payload) inkl. Gesamtzahl laden."""
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
    """Seitenweise Kaefer-Zeilen (schlankes Payload) inkl. Gesamtzahl laden."""
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
    """Kompakte Listenzeilen aus dem vorberechneten beetle_list_read laden."""
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
    """Gesamtzahl der kompakten Listenzeilen aus den vorberechneten Read-Modellen."""
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
    """Vorberechnete Gesamtzahl fuer ein einzelnes Filter-Dimension/Wert-Paar."""
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
    """Kompatibilitaets-Wrapper: laedt kompakte Zeilen und Gesamtzahl zusammen."""
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
    """Einen Detail-Datensatz einer GBIF-Beobachtung anhand der GBIF-ID laden."""
    return fetch_beetle_detail_row_by_entity(f"occ-{gbif_id}")


def fetch_beetle_detail_row_by_entity(entity_id: str) -> Optional[Dict[str, Any]]:
    """Einen Detail-Datensatz anhand der API-Entity-ID laden (occ-* oder rec-*)."""
    params: Dict[str, Any] = {"entity_id": entity_id}
    base_where_sql = ""
    media_where_sql = ""
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
    """Begrenzte Liste von Medieneintraegen einer Kaefer-Beobachtung laden."""
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
    """Seitenweise Medieneintraege samt Gesamtzahl einer Beobachtung laden."""
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
    """Laenderueberblick sowie Top-Klima-/Vegetations-Gruppen eines Landes laden."""
    params = {"country_code": country_code}
    with get_connection() as conn:
        overview = conn.execute(text(country_overview_sql()), params).mappings().first()
        climates = conn.execute(text(country_top_climates_sql()), params).mappings().all()
        vegetations = conn.execute(text(country_top_vegetation_sql()), params).mappings().all()
        koppen = conn.execute(text(country_top_koppen_sql()), params).mappings().all()
        vegetation_zones = conn.execute(text(country_top_vegetation_zone_sql()), params).mappings().all()
        top_beetles = conn.execute(text(country_top_beetles_sql()), params).mappings().all()

    return overview, climates, vegetations, koppen, vegetation_zones, top_beetles


def resolve_stored_country_value(candidates):
    """Liefert den tatsaechlich in location.country gespeicherten Wert aus einer
    Kandidatenliste (Name/ISO)."""
    values = [v for v in (candidates or []) if v]
    if not values:
        return None
    placeholders = ", ".join(f":c{i}" for i in range(len(values)))
    params = {f"c{i}": v for i, v in enumerate(values)}
    sql = text(
        f"SELECT country FROM location WHERE country IN ({placeholders}) LIMIT 1"
    )
    with get_connection() as conn:
        row = conn.execute(sql, params).first()
    return row[0] if row else None


def fetch_country_list_count(candidates):
    """Zaehlt die Funde eines Landes aus DEMSELBEN Read-Model wie die Ergebnisliste
    (beetle_list_read), damit die Panel-Zahl 'Funde' exakt mit der Listen-
    Trefferzahl uebereinstimmt (der rohe observation-Join weicht wegen
    Koordinaten-/Manuell-/Dedup-Regeln minimal ab)."""
    values = [v for v in (candidates or []) if v]
    if not values:
        return None
    placeholders = ", ".join(f":c{i}" for i in range(len(values)))
    params = {f"c{i}": v for i, v in enumerate(values)}
    sql = text(f"SELECT COUNT(*) FROM beetle_list_read WHERE country IN ({placeholders})")
    with get_connection() as conn:
        return int(conn.execute(sql, params).scalar() or 0)


def fetch_environment_ranges() -> Dict[str, Optional[float]]:
    """Globale Min-/Max-Werte der Umweltmetriken fuer die Detail-Balken laden.

    Die MIN/MAX-Spalten werden aus dem zentralen ENVIRONMENT_METRICS-Katalog
    erzeugt, damit sie mit dem Controller-Payload synchron bleiben.
    """
    cte_sql = full_enriched_cte_sql("")
    range_columns = ",\n            ".join(
        f"MIN(e.{column}) AS min_{column}, MAX(e.{column}) AS max_{column}"
        for column, _ in ENVIRONMENT_METRICS
    )
    sql = text(
        f"""
        {cte_sql}
        SELECT
            {range_columns}
        FROM enriched e
        """
    )

    with get_connection() as conn:
        row = conn.execute(sql).mappings().first()

    return dict(row) if row is not None else {}


def fetch_featured_beetle_rows():
    """Die manuell gepflegten Featured-Kaefer (record_id + Name) aus der DB laden.

    Dient als Quelle der Wahrheit fuer die rec-IDs, damit die statische
    frontend/data/featured-beetles.js nach einem DB-Neuaufbau nicht driftet.
    """
    sql = text(
        """
        SELECT br.record_id, br.scientific_name, br.family, br.precipitation
        FROM beetle_record br
        WHERE br.dataset_name = 'featured-beetles.js'
          AND br.status = 'active'
        ORDER BY br.record_id
        """
    )

    with get_connection() as conn:
        rows = conn.execute(sql).mappings().all()

    return [dict(row) for row in rows]
