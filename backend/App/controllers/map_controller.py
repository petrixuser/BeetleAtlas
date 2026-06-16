from typing import Any, Dict, List, Optional

from backend.App.controllers.beetle_controller import list_beetles_controller
from backend.App.controllers.core_controller import parse_bbox_or_error
from backend.App.repositories.map_repository import (
    _cluster_cell_size,
    build_map_geojson,
    build_map_points,
    cluster_map_points,
    fetch_map_clusters_lean,
    fetch_map_points_lean,
    map_sort_to_beetles_sort,
)


def _map_points_controller_lean(
    bbox: str,
    zoom: int,
    q: Optional[str],
    climate: Optional[str],
    vegetation: Optional[str],
    elevation: Optional[str],
    limit: int,
) -> Dict[str, Any]:
    """Fast path: only filters that derive from location/beetle_species columns.

    Skips the media aggregation and the correlated climate_snapshot subquery of
    the full beetle query, and clusters in SQL — turning the ~33s full-LatAm map
    query into a few seconds. The WHERE fragments reuse the e.*/l.* aliases that
    map_repository's lean CTEs expose.
    """
    filters: List[str] = []
    base_filters: List[str] = []
    params: Dict[str, Any] = {}

    if q:
        filters.append("(e.name LIKE :q OR e.family LIKE :q OR e.location LIKE :q)")
        params["q"] = f"%{q.strip()}%"
    if climate:
        filters.append("e.climate = :climate")
        params["climate"] = climate
    if vegetation:
        filters.append("e.vegetation = :vegetation")
        params["vegetation"] = vegetation
    if elevation:
        filters.append("e.elevationGroup = :elevation")
        params["elevation"] = elevation

    if bbox:
        params.update(parse_bbox_or_error(bbox))
        base_filters.append(
            "(l.longitude BETWEEN :min_lng AND :max_lng AND l.latitude BETWEEN :min_lat AND :max_lat)"
        )

    where_sql = ("WHERE " + " AND ".join(filters)) if filters else ""
    base_where_sql = ("WHERE " + " AND ".join(base_filters)) if base_filters else ""

    if zoom < 7:
        clusters = fetch_map_clusters_lean(
            base_where_sql=base_where_sql,
            where_sql=where_sql,
            cell=_cluster_cell_size(zoom),
            params=params,
        )
        return {
            "items": clusters,
            "total": len(clusters),
            "page": 1,
            "page_size": len(clusters),
            # Sum over all clusters = real number of matching points in the bbox
            # (SQL GROUP BY partitions every match, unlike the old 1000-row sample).
            "source_total_points": sum(cluster["count"] for cluster in clusters),
            "clustered": True,
        }

    points = fetch_map_points_lean(
        base_where_sql=base_where_sql,
        where_sql=where_sql,
        limit=limit,
        params=params,
    )
    # total is unused by the frontend; reporting the returned count keeps this a
    # single query (an exact COUNT over a large zoom-7 bbox would be wasteful).
    return {
        "items": points,
        "total": len(points),
        "page": 1,
        "page_size": limit,
        "clustered": False,
    }


def map_points_controller(
    bbox: str,
    zoom: int,
    q: Optional[str],
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
    basis_of_record_class: Optional[str],
    taxon_resolution: Optional[str],
    media_coverage: Optional[str],
    license_class: Optional[str],
    limit: int,
    offset: int,
    sort_by: str,
    sort_dir: str,
):
    # Only the common filters (q/climate/vegetation/elevation + bbox) are sent by
    # the frontend map. If no advanced band filter is present, take the lean path.
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
        basis_of_record_class,
        taxon_resolution,
        media_coverage,
        license_class,
    )
    if not any(advanced_filters):
        return _map_points_controller_lean(
            bbox=bbox,
            zoom=zoom,
            q=q,
            climate=climate,
            vegetation=vegetation,
            elevation=elevation,
            limit=limit,
        )

    beetles_sort_by = map_sort_to_beetles_sort(sort_by)

    beetles_result = list_beetles_controller(
        q=q,
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
        basis_of_record_class=basis_of_record_class,
        taxon_resolution=taxon_resolution,
        media_coverage=media_coverage,
        license_class=license_class,
        bbox=bbox,
        limit=limit,
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
    points_result = map_points_controller(**kwargs)
    return build_map_geojson(points_result)
