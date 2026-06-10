from math import floor
from typing import Any, Dict, List


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
