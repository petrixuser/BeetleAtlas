from math import floor
from typing import Any, Dict, List

from sqlalchemy import text

from backend.App.core.classifications import (
    CLIMATE_CASE_SQL,
    ELEVATION_GROUP_CASE_SQL,
    VEGETATION_CASE_SQL,
)
from backend.App.core.db import get_connection


def map_sort_to_beetles_sort(sort_by: str) -> str:
    return {
        "speciesName": "name",
        "observedAt": "observedAt",
        "elevation": "elevation",
        "climate": "climate",
        "vegetation": "vegetation",
    }[sort_by]


def build_map_points(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    points: List[Dict[str, Any]] = []
    for item in items:
        coords = item.get("coordinates") or [None, None]
        points.append(
            {
                "id": item.get("id"),
                "speciesName": item.get("name"),
                "lat": coords[1],
                "lng": coords[0],
                "elevation": item.get("elevation"),
                "climate": item.get("climate"),
                "vegetation": item.get("vegetation"),
                "observedAt": item.get("observedAt"),
                "isCluster": False,
            }
        )
    return points


def cluster_map_points(points: List[Dict[str, Any]], zoom: int) -> List[Dict[str, Any]]:
    cell = _cluster_cell_size(zoom)
    buckets: Dict[tuple, Dict[str, Any]] = {}

    for point in points:
        lat = point.get("lat")
        lng = point.get("lng")
        if lat is None or lng is None:
            continue

        row = floor(float(lat) / cell)
        col = floor(float(lng) / cell)
        key = (row, col)

        if key not in buckets:
            buckets[key] = {"lat_sum": 0.0, "lng_sum": 0.0, "count": 0}

        buckets[key]["lat_sum"] += float(lat)
        buckets[key]["lng_sum"] += float(lng)
        buckets[key]["count"] += 1

    clusters: List[Dict[str, Any]] = []
    for bucket in buckets.values():
        count = bucket["count"]
        clusters.append(
            {
                "lat": bucket["lat_sum"] / count,
                "lng": bucket["lng_sum"] / count,
                "count": count,
                "isCluster": True,
            }
        )

    clusters.sort(key=lambda item: item["count"], reverse=True)
    return clusters


def build_map_geojson(points_result: Dict[str, Any]) -> Dict[str, Any]:
    features: List[Dict[str, Any]] = []
    for item in points_result["items"]:
        lat = item.get("lat")
        lng = item.get("lng")
        if lat is None or lng is None:
            continue

        properties = {k: v for k, v in item.items() if k not in {"lat", "lng"}}
        features.append(
            {
                "type": "Feature",
                "geometry": {
                    "type": "Point",
                    "coordinates": [float(lng), float(lat)],
                },
                "properties": properties,
            }
        )

    return {
        "type": "FeatureCollection",
        "features": features,
        "meta": {
            "total": points_result.get("total", 0),
            "page": points_result.get("page", 1),
            "page_size": points_result.get("page_size", len(features)),
            "clustered": points_result.get("clustered", False),
            "source_total_points": points_result.get("source_total_points"),
        },
    }


def _cluster_cell_size(zoom: int) -> float:
    if zoom <= 2:
        return 4.0
    if zoom <= 4:
        return 2.0
    if zoom <= 6:
        return 1.0
    return 0.5


# --- Lean map queries -------------------------------------------------------
#
# The map only needs id/lat/lng/elevation/climate/vegetation/observedAt. climate
# derives from location.worldclim_bio01 and vegetation from location.landcover_class
# (see classifications.CLIMATE_CASE_SQL / VEGETATION_CASE_SQL), so neither the
# media aggregation nor the correlated climate_snapshot subquery of the full beetle
# query is required here. Dropping both — plus clustering in SQL instead of in
# Python over a 1000-row sample — turns the ~33s full-LatAm map query into a few
# seconds. Used by map_controller for the common filter set (q/climate/vegetation/
# elevation + bbox); advanced band filters fall back to the full beetle query.
#
# The base/enriched CTEs mirror the full query's aliases (b.* raw columns, e.*
# classified columns) so the same e.* / l.* WHERE fragments can be reused.

# Safety cap on returned clusters — populated grid cells are few, so this never
# truncates in practice; it just bounds a pathological response.
_MAX_CLUSTERS = 5000


def _map_base_cte(base_where_sql: str) -> str:
    return f"""
        WITH b AS (
            SELECT
                o.gbif_id,
                o.event_date,
                l.latitude AS lat,
                l.longitude AS lng,
                l.elevation,
                l.landcover_class,
                CASE
                    WHEN l.worldclim_bio01 IS NULL OR l.worldclim_bio01 = -9999 THEN NULL
                    WHEN l.worldclim_bio01 > 80 THEN l.worldclim_bio01 / 10
                    ELSE l.worldclim_bio01
                END AS worldclim_bio01,
                bs.scientific_name AS name,
                bs.family,
                COALESCE(
                    NULLIF(l.verbatim_locality, ''),
                    NULLIF(CONCAT_WS(', ', l.city, l.region, l.country), ''),
                    NULLIF(CONCAT_WS(', ', l.region, l.country), ''),
                    l.country,
                    'Unbekannt'
                ) AS location
            FROM observation o
            JOIN location l ON l.location_id = o.location_id
            JOIN beetle_species bs ON bs.beetle_id = o.beetle_id
            {base_where_sql}
        ),
        enriched AS (
            SELECT
                b.gbif_id,
                b.event_date AS observedAt,
                b.name,
                b.lat,
                b.lng,
                b.elevation,
                {CLIMATE_CASE_SQL} AS climate,
                {VEGETATION_CASE_SQL} AS vegetation,
                {ELEVATION_GROUP_CASE_SQL} AS elevationGroup,
                b.family,
                b.location
            FROM b
        )
    """


def fetch_map_clusters_lean(
    *,
    base_where_sql: str,
    where_sql: str,
    cell: float,
    params: Dict[str, Any],
) -> List[Dict[str, Any]]:
    sql = text(
        f"""
        {_map_base_cte(base_where_sql)}
        SELECT
            AVG(e.lat) AS lat,
            AVG(e.lng) AS lng,
            COUNT(*) AS count
        FROM enriched e
        {where_sql}
        GROUP BY FLOOR(e.lat / :cell), FLOOR(e.lng / :cell)
        ORDER BY count DESC
        LIMIT :max_clusters
        """
    )

    exec_params = dict(params)
    exec_params["cell"] = cell
    exec_params["max_clusters"] = _MAX_CLUSTERS

    with get_connection() as conn:
        rows = conn.execute(sql, exec_params).mappings().all()

    return [
        {
            "lat": float(row["lat"]),
            "lng": float(row["lng"]),
            "count": int(row["count"]),
            "isCluster": True,
        }
        for row in rows
    ]


def fetch_map_points_lean(
    *,
    base_where_sql: str,
    where_sql: str,
    limit: int,
    params: Dict[str, Any],
) -> List[Dict[str, Any]]:
    sql = text(
        f"""
        {_map_base_cte(base_where_sql)}
        SELECT
            e.gbif_id,
            e.name AS speciesName,
            e.lat,
            e.lng,
            e.elevation,
            e.climate,
            e.vegetation,
            e.observedAt
        FROM enriched e
        {where_sql}
        ORDER BY e.gbif_id
        LIMIT :limit
        """
    )

    exec_params = dict(params)
    exec_params["limit"] = limit

    with get_connection() as conn:
        rows = conn.execute(sql, exec_params).mappings().all()

    return [
        {
            "id": f"occ-{row['gbif_id']}",
            "speciesName": row["speciesName"],
            "lat": float(row["lat"]) if row["lat"] is not None else None,
            "lng": float(row["lng"]) if row["lng"] is not None else None,
            "elevation": int(round(row["elevation"])) if row["elevation"] is not None else 0,
            "climate": row["climate"],
            "vegetation": row["vegetation"],
            "observedAt": row["observedAt"],
            "isCluster": False,
        }
        for row in rows
    ]
