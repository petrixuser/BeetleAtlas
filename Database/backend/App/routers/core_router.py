from datetime import date
from typing import Optional

from fastapi import APIRouter, Query

from Database.Backend.App.controllers.core_controller import (
    climate_by_location_controller,
    compare_quality_report_history_controller,
    create_quality_report_snapshot_controller,
    healthcheck_controller,
    list_quality_report_history_controller,
    list_observations_controller,
    quality_report_controller,
    list_species_controller,
    stats_overview_controller,
)
from Database.Backend.App.core.field_mappings import FIELD_MAPPINGS
from Database.Backend.App.core.openapi_examples import (
    FILTERS_CORE_EXAMPLE,
    HEALTH_OK_EXAMPLE,
    QUALITY_HISTORY_COMPARE_EXAMPLE,
    QUALITY_HISTORY_LIST_EXAMPLE,
    QUALITY_HISTORY_SNAPSHOT_EXAMPLE,
    QUALITY_REPORT_EXAMPLE,
)
from Database.Backend.App.core.payloads import CORE_FILTER_OPTIONS, FILTER_OPTIONS


router = APIRouter()


@router.get(
    "/health",
    responses={
        200: {
            "description": "API health status.",
            "content": {"application/json": {"example": HEALTH_OK_EXAMPLE}},
        }
    },
)
def healthcheck():
    return healthcheck_controller()


@router.get("/stats/overview")
def stats_overview():
    return stats_overview_controller()


@router.get("/species")
def list_species(
    limit: int = Query(50, ge=1, le=500),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("beetle_id", pattern="^(beetle_id|scientific_name|family)$"),
    sort_dir: str = Query("asc", pattern="^(asc|desc)$"),
):
    return list_species_controller(limit=limit, offset=offset, sort_by=sort_by, sort_dir=sort_dir)


@router.get(
    "/api/filters",
    responses={
        200: {
            "description": "Available filter options for frontend.",
            "content": {"application/json": {"example": FILTERS_CORE_EXAMPLE}},
        }
    },
)
def list_frontend_filters(profile: str = Query("core", pattern="^(core|extended)$")):
    if profile == "extended":
        return FILTER_OPTIONS
    return CORE_FILTER_OPTIONS


@router.get("/api/field-mappings")
def list_field_mappings():
    return {"tables": FIELD_MAPPINGS}


@router.get(
    "/quality/report",
    responses={
        200: {
            "description": "Data quality and null-rate report.",
            "content": {"application/json": {"example": QUALITY_REPORT_EXAMPLE}},
        }
    },
)
def quality_report():
    return quality_report_controller()


@router.post(
    "/quality/report/history/snapshot",
    responses={
        200: {
            "description": "Creates and stores a quality report snapshot.",
            "content": {"application/json": {"example": QUALITY_HISTORY_SNAPSHOT_EXAMPLE}},
        }
    },
)
def create_quality_report_snapshot(
    source: Optional[str] = Query(None, min_length=1, max_length=128),
):
    return create_quality_report_snapshot_controller(source=source)


@router.get(
    "/quality/report/history",
    responses={
        200: {
            "description": "Lists stored quality report snapshots.",
            "content": {"application/json": {"example": QUALITY_HISTORY_LIST_EXAMPLE}},
        }
    },
)
def list_quality_report_history(
    limit: int = Query(20, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    return list_quality_report_history_controller(limit=limit, offset=offset)


@router.get(
    "/quality/report/history/compare",
    responses={
        200: {
            "description": "Compares two quality report snapshots and returns deltas.",
            "content": {"application/json": {"example": QUALITY_HISTORY_COMPARE_EXAMPLE}},
        }
    },
)
def compare_quality_report_history(
    from_id: int = Query(..., ge=1),
    to_id: int = Query(..., ge=1),
):
    return compare_quality_report_history_controller(from_id=from_id, to_id=to_id)


@router.get("/observations")
def list_observations(
    beetle_id: Optional[int] = None,
    year: Optional[int] = Query(None, ge=1800, le=2100),
    has_image: Optional[bool] = None,
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    sort_by: str = Query("gbif_id", pattern="^(gbif_id|event_date|beetle_id)$"),
    sort_dir: str = Query("asc", pattern="^(asc|desc)$"),
):
    return list_observations_controller(
        beetle_id=beetle_id,
        year=year,
        has_image=has_image,
        limit=limit,
        offset=offset,
        sort_by=sort_by,
        sort_dir=sort_dir,
    )


@router.get("/climate/location/{location_id}")
def climate_by_location(
    location_id: int,
    from_date: Optional[date] = None,
    to_date: Optional[date] = None,
    limit: int = Query(500, ge=1, le=5000),
):
    return climate_by_location_controller(
        location_id=location_id,
        from_date=from_date,
        to_date=to_date,
        limit=limit,
    )
