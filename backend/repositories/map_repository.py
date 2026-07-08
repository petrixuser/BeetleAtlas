"""Repository fuer Kartenpunkte und Cluster-Aggregation."""
from math import floor
from typing import Any, Dict, List

from sqlalchemy import text

from backend.config.sql.map_repository_sql import (
    MAX_CLUSTERS,
    list_read_map_clusters_sql,
    list_read_map_points_sql,
    list_read_map_points_total_sql,
    map_clusters_sql,
    map_points_sql,
    map_points_total_sql,
)
from backend.core.db import get_connection

def map_sort_to_beetles_sort(sort_by: str) -> str:
    """Bildet den Karten-Sortierschluessel auf die entsprechende Kaefer-Spalte ab."""
    return {
        "speciesName": "name",
        "observedAt": "observedAt",
        "elevation": "elevation",
        "climate": "climate",
        "vegetation": "vegetation",
    }[sort_by]

def build_map_points(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Baut aus Beobachtungen Kartenpunkte (Name, Koordinaten, Umweltattribute)."""
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
    """Fasst Kartenpunkte je Zoomstufe zu Clustern zusammen (Mittelwert + Anzahl)."""
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
    """Baut aus Kartenpunkten eine GeoJSON-FeatureCollection samt Metadaten."""
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
    """Liefert die Rasterzellengroesse fuers Clustering je nach Zoomstufe."""
    if zoom <= 2:
        return 4.0
    if zoom <= 4:
        return 2.0
    if zoom <= 6:
        return 1.0
    return 0.5

def fetch_map_clusters_lean(
    *,
    base_where_sql: str,
    where_sql: str,
    cell: float,
    params: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Fuehrt die Cluster-Abfrage (map_point_read) aus und liefert die Cluster-Liste."""
    sql = text(map_clusters_sql(base_where_sql, where_sql))

    exec_params = dict(params)
    exec_params["cell"] = cell
    exec_params["max_clusters"] = MAX_CLUSTERS

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
    offset: int,
    params: Dict[str, Any],
) -> tuple[List[Dict[str, Any]], int]:
    """Fuehrt die Abfrage einzelner Kartenpunkte (map_point_read) samt Gesamtzahl aus."""
    sql = text(map_points_sql(base_where_sql, where_sql))
    total_sql = text(map_points_total_sql(base_where_sql, where_sql))

    exec_params = dict(params)
    exec_params["limit"] = limit
    exec_params["offset"] = offset

    with get_connection() as conn:
        total_row = conn.execute(total_sql, params).mappings().first()
        total = int(total_row["total"]) if total_row and total_row.get("total") is not None else 0
        rows = conn.execute(sql, exec_params).mappings().all()

    points = [
        {
            "id": row.get("entity_id") or (f"occ-{row['gbif_id']}" if row.get("gbif_id") is not None else None),
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
    return points, total


def fetch_map_clusters_from_list_read(
    *,
    where_sql: str,
    cell: float,
    params: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """Cluster ueber beetle_list_read fuer Read-Model-Filter (z. B. has_image /
    observed_year), die map_point_read nicht abbilden kann."""
    sql = text(list_read_map_clusters_sql(where_sql))

    exec_params = dict(params)
    exec_params["cell"] = cell
    exec_params["max_clusters"] = MAX_CLUSTERS

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


def fetch_map_points_from_list_read(
    *,
    where_sql: str,
    limit: int,
    offset: int,
    params: Dict[str, Any],
) -> tuple[List[Dict[str, Any]], int]:
    """Ungeclusterte Kartenpunkte ueber beetle_list_read fuer Read-Model-Filter."""
    sql = text(list_read_map_points_sql(where_sql))
    total_sql = text(list_read_map_points_total_sql(where_sql))

    exec_params = dict(params)
    exec_params["limit"] = limit
    exec_params["offset"] = offset

    with get_connection() as conn:
        total_row = conn.execute(total_sql, params).mappings().first()
        total = int(total_row["total"]) if total_row and total_row.get("total") is not None else 0
        rows = conn.execute(sql, exec_params).mappings().all()

    points = [
        {
            "id": row.get("entity_id") or (f"occ-{row['gbif_id']}" if row.get("gbif_id") is not None else None),
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
    return points, total
