from typing import Optional

from Database.Backend.App.controllers.beetle_controller import list_beetles_controller
from Database.Backend.App.repositories.map_repository import (
    build_map_geojson,
    build_map_points,
    cluster_map_points,
    map_sort_to_beetles_sort,
)


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
