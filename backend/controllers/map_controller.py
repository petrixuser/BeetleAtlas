"""Controller-Funktionen fuer die Karte: Punkte und Cluster je nach Zoom,
Klima-Subtyp-Geometrien, GeoJSON-Ausgabe und Karten-Antwort-Cache."""

from collections import OrderedDict
import json
from pathlib import Path
from threading import Lock
from typing import Any, Dict, List, Optional, Tuple

from backend.config.climate_subtypes import is_climate_subtype_code, parent_climate_code
from backend.config.country_aliases import country_filter_candidates
from backend.controllers.beetle_controller import build_read_model_where, list_beetles_controller
from backend.controllers.core_controller import parse_bbox_or_error
from backend.core.beetle_filter_helpers import append_climate_filter, append_vegetation_filter
from backend.repositories.map_repository import (
    _cluster_cell_size,
    build_map_geojson,
    build_map_points,
    cluster_map_points,
    fetch_map_clusters_from_list_read,
    fetch_map_clusters_lean,
    fetch_map_points_from_list_read,
    fetch_map_points_lean,
    map_sort_to_beetles_sort,
)


_MAP_RESPONSE_CACHE_MAX_ITEMS = 512
_map_response_cache: "OrderedDict[Tuple[Any, ...], Dict[str, Any]]" = OrderedDict()
_map_response_cache_lock = Lock()
_MAP_POINTS_MAX_PAGE_SIZE = 200

_subtype_geometries_lock = Lock()
_subtype_geometries_loaded = False
_subtype_geometries: Dict[str, List[Dict[str, Any]]] = {}


def _freeze_params(value: Any) -> Any:
    """Wandelt dicts/lists rekursiv in hashbare Tupel um (fuer Cache-Keys)."""
    if isinstance(value, dict):
        return tuple(sorted((k, _freeze_params(v)) for k, v in value.items()))
    if isinstance(value, list):
        return tuple(_freeze_params(v) for v in value)
    return value


def _cache_key_from_lean_args(**kwargs: Any) -> Tuple[Any, ...]:
    """Baut einen stabilen, hashbaren Cache-Key aus den uebergebenen Argumenten."""
    return tuple(sorted((k, _freeze_params(v)) for k, v in kwargs.items()))


def _cache_get(key: Tuple[Any, ...]) -> Optional[Dict[str, Any]]:
    """Liest einen Eintrag aus dem Karten-Antwort-Cache (LRU-Aktualisierung)."""
    with _map_response_cache_lock:
        value = _map_response_cache.get(key)
        if value is None:
            return None
        _map_response_cache.move_to_end(key)
        return value


def _cache_set(key: Tuple[Any, ...], value: Dict[str, Any]) -> None:
    """Schreibt einen Eintrag in den Karten-Antwort-Cache und verdraengt aelteste (LRU)."""
    with _map_response_cache_lock:
        _map_response_cache[key] = value
        _map_response_cache.move_to_end(key)
        while len(_map_response_cache) > _MAP_RESPONSE_CACHE_MAX_ITEMS:
            _map_response_cache.popitem(last=False)


def clear_map_response_cache() -> None:
    """Leert alle gecachten Karten-Antworten."""
    with _map_response_cache_lock:
        _map_response_cache.clear()


def _append_exact_or_in_filter(
    filters: List[str],
    params: Dict[str, Any],
    column: str,
    key: str,
    raw_value: Optional[str],
) -> None:
    """Haengt einen Exact- oder IN-Filter fuer optionale, kommaseparierte Query-Parameter an."""
    if not raw_value:
        return
    values = [part.strip() for part in str(raw_value).split(",") if part.strip()]
    if not values:
        return
    if len(values) == 1:
        filters.append(f"{column} = :{key}")
        params[key] = values[0]
        return

    placeholders: List[str] = []
    for idx, value in enumerate(values):
        param_key = f"{key}_{idx}"
        placeholders.append(f":{param_key}")
        params[param_key] = value
    filters.append(f"{column} IN ({', '.join(placeholders)})")


def _point_on_segment(px: float, py: float, x1: float, y1: float, x2: float, y2: float) -> bool:
    """Prueft, ob der Punkt (px, py) auf der Strecke zwischen zwei Punkten liegt."""
    cross = (px - x1) * (y2 - y1) - (py - y1) * (x2 - x1)
    if abs(cross) > 1e-12:
        return False
    dot = (px - x1) * (px - x2) + (py - y1) * (py - y2)
    return dot <= 1e-12


def _point_in_ring(px: float, py: float, ring: List[Tuple[float, float]]) -> bool:
    """Prueft per Ray-Casting, ob ein Punkt innerhalb eines Polygon-Rings liegt."""
    inside = False
    j = len(ring) - 1
    for i in range(len(ring)):
        xi, yi = ring[i]
        xj, yj = ring[j]

        if _point_on_segment(px, py, xi, yi, xj, yj):
            return True

        intersects = ((yi > py) != (yj > py)) and (
            px < ((xj - xi) * (py - yi) / ((yj - yi) or 1e-15) + xi)
        )
        if intersects:
            inside = not inside
        j = i
    return inside


def _normalize_ring(raw_ring: Any) -> List[Tuple[float, float]]:
    """Normalisiert einen rohen GeoJSON-Ring zu einer Liste von (lng, lat)-Tupeln."""
    ring: List[Tuple[float, float]] = []
    if not isinstance(raw_ring, list):
        return ring

    for point in raw_ring:
        if not isinstance(point, list) or len(point) < 2:
            continue
        try:
            lng = float(point[0])
            lat = float(point[1])
        except (TypeError, ValueError):
            continue
        ring.append((lng, lat))
    return ring


def _build_polygon_geometry(raw_polygon: Any) -> Optional[Dict[str, Any]]:
    """Baut aus rohen GeoJSON-Ringen eine Polygon-Geometrie mit outer, holes und bbox."""
    if not isinstance(raw_polygon, list) or not raw_polygon:
        return None

    rings: List[List[Tuple[float, float]]] = []
    for raw_ring in raw_polygon:
        ring = _normalize_ring(raw_ring)
        if len(ring) >= 3:
            rings.append(ring)

    if not rings:
        return None

    outer = rings[0]
    holes = rings[1:]
    lngs = [p[0] for p in outer]
    lats = [p[1] for p in outer]

    return {
        "outer": outer,
        "holes": holes,
        "bbox": (min(lngs), min(lats), max(lngs), max(lats)),
    }


def _load_climate_subtype_geometries() -> None:
    """Laedt und cacht die Koeppen-Subtyp-Polygone aus der LATAM-GeoJSON-Datei (einmalig)."""
    global _subtype_geometries_loaded

    if _subtype_geometries_loaded:
        return

    with _subtype_geometries_lock:
        if _subtype_geometries_loaded:
            return

        geojson_path = Path(__file__).resolve().parents[2] / "frontend" / "assets" / "koppen-latam.geojson"
        if not geojson_path.exists():
            _subtype_geometries_loaded = True
            return

        with geojson_path.open("r", encoding="utf-8") as f:
            payload = json.load(f)

        for feature in payload.get("features", []):
            props = feature.get("properties") or {}
            code = props.get("code")
            if not isinstance(code, str) or not is_climate_subtype_code(code):
                continue
            _subtype_geometries.setdefault(code, [])

            geometry = feature.get("geometry") or {}
            geom_type = geometry.get("type")
            coords = geometry.get("coordinates")
            if not isinstance(coords, list):
                continue

            if geom_type == "Polygon":
                polygon = _build_polygon_geometry(coords)
                if polygon is not None:
                    _subtype_geometries[code].append(polygon)
            elif geom_type == "MultiPolygon":
                for raw_polygon in coords:
                    polygon = _build_polygon_geometry(raw_polygon)
                    if polygon is not None:
                        _subtype_geometries[code].append(polygon)

        _subtype_geometries_loaded = True


def _point_in_polygon(lng: float, lat: float, polygon: Dict[str, Any]) -> bool:
    """Prueft, ob (lng, lat) im Polygon liegt (bbox-Vorfilter, outer-Ring, Loecher)."""
    min_lng, min_lat, max_lng, max_lat = polygon["bbox"]
    if lng < min_lng or lng > max_lng or lat < min_lat or lat > max_lat:
        return False

    if not _point_in_ring(lng, lat, polygon["outer"]):
        return False

    for hole in polygon["holes"]:
        if _point_in_ring(lng, lat, hole):
            return False
    return True


def _matches_any_subtype(point: Dict[str, Any], subtypes: List[str]) -> bool:
    """Prueft, ob ein Kartenpunkt in einem der angegebenen Klima-Subtyp-Polygone liegt."""
    lng = point.get("lng")
    lat = point.get("lat")
    if lng is None or lat is None:
        return False

    try:
        lng_f = float(lng)
        lat_f = float(lat)
    except (TypeError, ValueError):
        return False

    for subtype in subtypes:
        for polygon in _subtype_geometries.get(subtype, []):
            if _point_in_polygon(lng_f, lat_f, polygon):
                return True
    return False


def _parse_climate_filter(raw_climate: Optional[str]) -> Tuple[Optional[str], List[str]]:
    """Zerlegt den Klima-Filter in Hauptgruppen-CSV und Liste der Subtyp-Codes."""
    if not raw_climate:
        return None, []

    raw_values = [part.strip() for part in str(raw_climate).split(",") if part.strip()]
    if not raw_values:
        return None, []

    majors: List[str] = []
    subtypes: List[str] = []

    for value in raw_values:
        if is_climate_subtype_code(value):
            subtypes.append(value)
            parent = parent_climate_code(value)
            if parent and parent not in majors:
                majors.append(parent)
            continue
        if value not in majors:
            majors.append(value)

    major_climate = ",".join(majors) if majors else None
    return major_climate, subtypes


def _fetch_all_points_lean(
    *,
    base_where_sql: str,
    where_sql: str,
    params: Dict[str, Any],
    page_size: int = 5000,
) -> List[Dict[str, Any]]:
    """Laedt seitenweise alle passenden Kartenpunkte (lean) und sammelt sie in einer Liste."""
    all_points: List[Dict[str, Any]] = []
    offset = 0

    while True:
        page_points, total_points = fetch_map_points_lean(
            base_where_sql=base_where_sql,
            where_sql=where_sql,
            limit=page_size,
            offset=offset,
            params=params,
        )
        if not page_points:
            break

        all_points.extend(page_points)
        offset += len(page_points)
        if len(all_points) >= total_points:
            break

    return all_points


def _build_lean_where_and_params(
    *,
    bbox: str,
    q: Optional[str],
    country: Optional[str],
    climate: Optional[str],
    vegetation: Optional[str],
    elevation: Optional[str],
) -> Tuple[str, str, Dict[str, Any]]:
    """Baut WHERE-/base-WHERE-Klauseln und Params fuer den schlanken Karten-Pfad."""
    base_filters: List[str] = []
    filters: List[str] = []
    params: Dict[str, Any] = {}

    if q:
        base_filters.append("(b.name LIKE :q OR b.family LIKE :q OR b.location LIKE :q)")
        params["q"] = f"%{q.strip()}%"
    append_climate_filter(filters, params, "e.climate", climate, "e.koppen_code")
    if country:
        # Land gemischt gespeichert (Name vs. ISO) -> auf alle Varianten matchen.
        cands = country_filter_candidates(country)
        if cands:
            keys = []
            for idx, cand in enumerate(cands):
                pkey = f"country_{idx}"
                params[pkey] = cand
                keys.append(f":{pkey}")
            base_filters.append(f"b.country IN ({', '.join(keys)})")
    append_vegetation_filter(filters, params, "e.vegetation", vegetation, "e.vegetation_zone")
    _append_exact_or_in_filter(filters, params, "e.elevationGroup", "elevation", elevation)

    if bbox:
        params.update(parse_bbox_or_error(bbox))
        base_filters.append("(b.lng BETWEEN :min_lng AND :max_lng AND b.lat BETWEEN :min_lat AND :max_lat)")

    where_sql = ("WHERE " + " AND ".join(filters)) if filters else ""
    base_where_sql = ("WHERE " + " AND ".join(base_filters)) if base_filters else ""
    return where_sql, base_where_sql, params


def _build_subtype_filtered_result(
    *,
    zoom: int,
    limit: int,
    offset: int,
    subtype_climates: List[str],
    base_where_sql: str,
    where_sql: str,
    params: Dict[str, Any],
) -> Dict[str, Any]:
    """Filtert Punkte per Subtyp-Geometrie und liefert Cluster (zoom < 7) oder eine Punkt-Seite."""
    effective_limit = max(1, min(int(limit), _MAP_POINTS_MAX_PAGE_SIZE))
    _load_climate_subtype_geometries()
    points = _fetch_all_points_lean(
        base_where_sql=base_where_sql,
        where_sql=where_sql,
        params=params,
        page_size=5000,
    )
    filtered_points = [p for p in points if _matches_any_subtype(p, subtype_climates)]

    if zoom < 7:
        clusters = cluster_map_points(filtered_points, zoom)
        return {
            "items": clusters,
            "total": len(clusters),
            "page": 1,
            "page_size": len(clusters),
            "source_total_points": len(filtered_points),
            "clustered": True,
        }

    page_items = filtered_points[offset : offset + effective_limit]
    return {
        "items": page_items,
        "total": len(filtered_points),
        "page": 1,
        "page_size": effective_limit,
        "clustered": False,
    }

def _map_points_controller_lean(
    bbox: str,
    zoom: int,
    q: Optional[str],
    country: Optional[str],
    climate: Optional[str],
    vegetation: Optional[str],
    elevation: Optional[str],
    limit: int,
    offset: int,
) -> Dict[str, Any]:
    """Schneller Karten-Punkt-Pfad ausschliesslich fuer bbox und Basis-Filter.

    Nutzt schlanke SQL-Queries und gibt je nach Zoom Cluster (zoom < 7) oder Punkte zurueck.
    """

    effective_limit = max(1, min(int(limit), _MAP_POINTS_MAX_PAGE_SIZE))
    normalized_climate, subtype_climates = _parse_climate_filter(climate)
    where_sql, base_where_sql, params = _build_lean_where_and_params(
        bbox=bbox,
        q=q,
        country=country,
        climate=climate,
        vegetation=vegetation,
        elevation=elevation,
    )

    cache_key = _cache_key_from_lean_args(
        bbox=bbox,
        zoom=zoom,
        q=q,
        country=country,
        climate=climate,
        normalized_climate=normalized_climate,
        subtype_climates=subtype_climates,
        vegetation=vegetation,
        elevation=elevation,
        limit=effective_limit,
        offset=offset,
    )
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    if zoom < 7:
        clusters = fetch_map_clusters_lean(
            base_where_sql=base_where_sql,
            where_sql=where_sql,
            cell=_cluster_cell_size(zoom),
            params=params,
        )
        result = {
            "items": clusters,
            "total": len(clusters),
            "page": 1,
            "page_size": len(clusters),
            "source_total_points": sum(cluster["count"] for cluster in clusters),
            "clustered": True,
        }
        _cache_set(cache_key, result)
        return result

    points, total_points = fetch_map_points_lean(
        base_where_sql=base_where_sql,
        where_sql=where_sql,
        limit=effective_limit,
        offset=offset,
        params=params,
    )
    result = {
        "items": points,
        "total": total_points,
        "page": 1,
        "page_size": effective_limit,
        "clustered": False,
    }
    _cache_set(cache_key, result)
    return result


def _map_points_controller_from_list_read(
    *,
    bbox: str,
    zoom: int,
    q: Optional[str],
    country: Optional[str],
    climate: Optional[str],
    vegetation: Optional[str],
    elevation: Optional[str],
    soil_ph_band: Optional[str],
    temperature_band: Optional[str],
    precipitation_band: Optional[str],
    event_date_quality: Optional[str],
    observed_year: Optional[int],
    has_image: Optional[bool],
    limit: int,
    offset: int,
) -> Dict[str, Any]:
    """Karten-Punkte/-Cluster fuer Read-Model-gestuetzte Filter ueber eine
    Aggregation des gesamten Datensatzes von beetle_list_read."""
    effective_limit = max(1, min(int(limit), _MAP_POINTS_MAX_PAGE_SIZE))
    cache_key = _cache_key_from_lean_args(
        path="list_read",
        bbox=bbox,
        zoom=zoom,
        q=q,
        country=country,
        climate=climate,
        vegetation=vegetation,
        elevation=elevation,
        soil_ph_band=soil_ph_band,
        temperature_band=temperature_band,
        precipitation_band=precipitation_band,
        event_date_quality=event_date_quality,
        observed_year=observed_year,
        has_image=has_image,
        limit=effective_limit,
        offset=offset,
    )
    cached = _cache_get(cache_key)
    if cached is not None:
        return cached

    where_sql, params = build_read_model_where(
        q=q,
        country=country,
        climate=climate,
        vegetation=vegetation,
        elevation=elevation,
        soil_ph_band=soil_ph_band,
        temperature_band=temperature_band,
        precipitation_band=precipitation_band,
        event_date_quality=event_date_quality,
        observed_year=observed_year,
        has_image=has_image,
        bbox=bbox,
    )

    if zoom < 7:
        clusters = fetch_map_clusters_from_list_read(
            where_sql=where_sql,
            cell=_cluster_cell_size(zoom),
            params=params,
        )
        result = {
            "items": clusters,
            "total": len(clusters),
            "page": 1,
            "page_size": len(clusters),
            "source_total_points": sum(cluster["count"] for cluster in clusters),
            "clustered": True,
        }
        _cache_set(cache_key, result)
        return result

    points, total_points = fetch_map_points_from_list_read(
        where_sql=where_sql,
        limit=effective_limit,
        offset=offset,
        params=params,
    )
    result = {
        "items": points,
        "total": total_points,
        "page": (offset // effective_limit) + 1,
        "page_size": effective_limit,
        "clustered": False,
    }
    _cache_set(cache_key, result)
    return result


def warm_map_points_cache() -> None:
    """Berechnet haeufige Klima-Gruppen-Kartenabfragen beim Start vor, fuer eine schnellere erste Nutzung."""
    latam_bbox = "-120,-60,-30,35"
    for climate_code in ["A", "B", "C", "D", "E"]:
        try:
            _map_points_controller_lean(
                bbox=latam_bbox,
                zoom=7,
                q=None,
                country=None,
                climate=climate_code,
                vegetation=None,
                elevation=None,
                limit=5000,
                offset=0,
            )
        except Exception:
            continue

def map_points_controller(
    bbox: str,
    zoom: int,
    q: Optional[str],
    country: Optional[str],
    climate: Optional[str],
    vegetation: Optional[str],
    elevation: Optional[str],
    temperature_band: Optional[str],
    precipitation_band: Optional[str],
    soil_moisture_band: Optional[str],
    ndvi_band: Optional[str],
    humidity_band: Optional[str],
    pressure_band: Optional[str],
    light_pollution_band: Optional[str],
    slope_band: Optional[str],
    water_distance_band: Optional[str],
    human_impact_band: Optional[str],
    landcover_group: Optional[str],
    coordinate_uncertainty_band: Optional[str],
    soil_ph_band: Optional[str],
    soil_carbon_band: Optional[str],
    worldclim_temp_band: Optional[str],
    worldclim_precip_band: Optional[str],
    event_date_quality: Optional[str],
    observed_year: Optional[int],
    basis_of_record_class: Optional[str],
    taxon_resolution: Optional[str],
    media_coverage: Optional[str],
    has_image: Optional[bool],
    license_class: Optional[str],
    limit: int,
    offset: int,
    sort_by: str,
    sort_dir: str,
):
    """Gibt Karten-Punkte oder -Cluster fuer den aktuellen Viewport und die Filter zurueck."""
    effective_limit = max(1, min(int(limit), _MAP_POINTS_MAX_PAGE_SIZE))
    advanced_filters = (
        temperature_band,
        precipitation_band,
        soil_moisture_band,
        ndvi_band,
        humidity_band,
        pressure_band,
        light_pollution_band,
        slope_band,
        water_distance_band,
        human_impact_band,
        landcover_group,
        coordinate_uncertainty_band,
        soil_ph_band,
        soil_carbon_band,
        worldclim_temp_band,
        worldclim_precip_band,
        event_date_quality,
        observed_year,
        basis_of_record_class,
        taxon_resolution,
        media_coverage,
        has_image,
        license_class,
    )
    if not any(advanced_filters):
        return _map_points_controller_lean(
            bbox=bbox,
            zoom=zoom,
            q=q,
            country=country,
            climate=climate,
            vegetation=vegetation,
            elevation=elevation,
            limit=effective_limit,
            offset=offset,
        )

    live_only_advanced = (
        soil_moisture_band,
        ndvi_band,
        humidity_band,
        pressure_band,
        light_pollution_band,
        slope_band,
        water_distance_band,
        human_impact_band,
        landcover_group,
        coordinate_uncertainty_band,
        soil_carbon_band,
        worldclim_temp_band,
        worldclim_precip_band,
        basis_of_record_class,
        taxon_resolution,
        media_coverage,
        license_class,
    )
    if not any(live_only_advanced):
        return _map_points_controller_from_list_read(
            bbox=bbox,
            zoom=zoom,
            q=q,
            country=country,
            climate=climate,
            vegetation=vegetation,
            elevation=elevation,
            soil_ph_band=soil_ph_band,
            temperature_band=temperature_band,
            precipitation_band=precipitation_band,
            event_date_quality=event_date_quality,
            observed_year=observed_year,
            has_image=has_image,
            limit=effective_limit,
            offset=offset,
        )

    beetles_sort_by = map_sort_to_beetles_sort(sort_by)

    beetles_result = list_beetles_controller(
        q=q,
        country=country,
        climate=climate,
        vegetation=vegetation,
        elevation=elevation,
        temperature_band=temperature_band,
        precipitation_band=precipitation_band,
        soil_moisture_band=soil_moisture_band,
        ndvi_band=ndvi_band,
        humidity_band=humidity_band,
        pressure_band=pressure_band,
        light_pollution_band=light_pollution_band,
        slope_band=slope_band,
        water_distance_band=water_distance_band,
        human_impact_band=human_impact_band,
        landcover_group=landcover_group,
        coordinate_uncertainty_band=coordinate_uncertainty_band,
        soil_ph_band=soil_ph_band,
        soil_carbon_band=soil_carbon_band,
        worldclim_temp_band=worldclim_temp_band,
        worldclim_precip_band=worldclim_precip_band,
        event_date_quality=event_date_quality,
        observed_year=observed_year,
        basis_of_record_class=basis_of_record_class,
        taxon_resolution=taxon_resolution,
        media_coverage=media_coverage,
        has_image=has_image,
        license_class=license_class,
        bbox=bbox,
        limit=effective_limit,
        offset=offset,
        sort_by=beetles_sort_by,
        sort_dir=sort_dir,
    )

    points = build_map_points(beetles_result["items"])

    if zoom < 7:
        clusters = cluster_map_points(points, zoom)
        return {
            "items": clusters,
            "total": len(clusters),
            "page": 1,
            "page_size": len(clusters),
            "source_total_points": beetles_result["total"],
            "clustered": True,
        }

    return {
        "items": points,
        "total": beetles_result["total"],
        "page": beetles_result["page"],
        "page_size": beetles_result["page_size"],
        "clustered": False,
    }

def map_points_geojson_controller(**kwargs):
    """Gibt Karten-Punkte als GeoJSON-FeatureCollection zurueck.

    Nutzt die Ausgabe des Karten-Punkt-Controllers wieder und wandelt sie in GeoJSON um.
    """
    points_result = map_points_controller(**kwargs)
    return build_map_geojson(points_result)
