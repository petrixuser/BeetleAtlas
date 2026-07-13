"""API-Router fuer Karten-Endpunkte: Punkte/Cluster und GeoJSON-Ausgabe."""

from fastapi import APIRouter, Depends

from backend.controllers.map_controller import (
    map_points_controller,
    map_points_geojson_controller,
)
from backend.routers.openapi_examples import (
    MAP_POINTS_EXAMPLE,
    MAP_POINTS_GEOJSON_EXAMPLE,
)
from backend.config.query_params import map_query_params


router = APIRouter()

@router.get(
    "/api/map/points",
    responses={
        200: {
            "description": "Map points or clusters depending on zoom level.",
            "content": {"application/json": {"example": MAP_POINTS_EXAMPLE}},
        }
    },
)
def map_points(params: dict = Depends(map_query_params)):
    """Gibt Karten-Punkte oder -Cluster abhaengig von Zoom und Filtern zurueck."""
    return map_points_controller(**params)

@router.get(
    "/api/map/points/geojson",
    responses={
        200: {
            "description": "Map points as GeoJSON FeatureCollection.",
            "content": {"application/json": {"example": MAP_POINTS_GEOJSON_EXAMPLE}},
        }
    },
)
def map_points_geojson(params: dict = Depends(map_query_params)):
    """Gibt Karten-Punkte als GeoJSON-FeatureCollection zurueck."""
    return map_points_geojson_controller(**params)
