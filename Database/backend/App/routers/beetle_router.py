from fastapi import APIRouter, Depends, Query

from Database.Backend.App.controllers.beetle_controller import (
    get_beetle_by_id_controller,
    get_beetle_media_controller,
    get_country_detail_controller,
    list_beetles_controller,
)
from Database.Backend.App.core.openapi_examples import (
    BEETLE_DETAIL_EXAMPLE,
    BEETLE_MEDIA_EXAMPLE,
    BEETLES_LIST_EXAMPLE,
    COUNTRY_DETAIL_EXAMPLE,
)
from Database.Backend.App.routers.query_params import beetle_query_params


router = APIRouter()


@router.get(
    "/api/beetles",
    responses={
        200: {
            "description": "Filtered beetle list with pagination.",
            "content": {"application/json": {"example": BEETLES_LIST_EXAMPLE}},
        }
    },
)
def list_beetles(params: dict = Depends(beetle_query_params)):
    return list_beetles_controller(**params)


@router.get(
    "/api/beetles/{beetle_id}",
    responses={
        200: {
            "description": "Single beetle entry.",
            "content": {"application/json": {"example": BEETLE_DETAIL_EXAMPLE}},
        }
    },
)
def get_beetle_by_id(beetle_id: str):
    return get_beetle_by_id_controller(beetle_id)


@router.get(
    "/api/beetles/{beetle_id}/media",
    responses={
        200: {
            "description": "Paginated media list for a beetle observation.",
            "content": {"application/json": {"example": BEETLE_MEDIA_EXAMPLE}},
        }
    },
)
def get_beetle_media(
    beetle_id: str,
    limit: int = Query(20, ge=1, le=200),
    offset: int = Query(0, ge=0),
):
    return get_beetle_media_controller(beetle_id=beetle_id, limit=limit, offset=offset)


@router.get(
    "/api/countries/{country_code}",
    responses={
        200: {
            "description": "Country detail summary.",
            "content": {"application/json": {"example": COUNTRY_DETAIL_EXAMPLE}},
        }
    },
)
def get_country_detail(country_code: str):
    return get_country_detail_controller(country_code)
