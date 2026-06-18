from math import floor
from typing import Any, Dict, List

from sqlalchemy import text

from backend.config.map_repository_sql import (
    MAX_CLUSTERS,
    map_clusters_sql,
    map_points_sql,
)
from backend.core.db import get_connection

def map_sort_to_beetles_sort(sort_by: str) -> str:
    """Sorts the map points based on the specified sort_by parameter, mapping it to the corresponding column in the beetle database."""
    return {
        "speciesName": "name",
        "observedAt": "observedAt",
        "elevation": "elevation",
        "climate": "climate",
        "vegetation": "vegetation",
    }[sort_by]

def build_map_points(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """This function takes a list of beetle observation items and builds a list of map points with relevant information such as species name, latitude, longitude, elevation, climate, vegetation, and observed date."""
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
    """This function takes a list of map points and clusters them based on the specified zoom level. calculating the average latitude and longitude for each cluster and counting the number of points in each cluster."""
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
    """This function takes a list of map points and builds a GeoJSON FeatureCollection with the relevant properties for each point, including metadata about the total number of points, pagination, and clustering status."""
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
    """This function determines the appropriate cell size for clustering map points based on the current zoom level, with predefined thresholds for different zoom levels."""
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
    """This function executes a SQL query to fetch clustered map points based on the provided base WHERE clause, additional WHERE clause, cell size for clustering, and query parameters. It returns a list of clusters with their average latitude, longitude, count of points, and cluster status."""
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
    params: Dict[str, Any],
) -> List[Dict[str, Any]]:
    """This function executes a SQL query to fetch individual map points based on the provided base WHERE clause, additional WHERE clause, limit, and query parameters."""
    sql = text(map_points_sql(base_where_sql, where_sql))

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
