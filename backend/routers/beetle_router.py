"""API-Router fuer lesende Kaefer-Endpunkte: Liste, Detail, Medien,
Umwelt-Wertebereiche und Laender-Zusammenfassungen."""

from fastapi import APIRouter, Depends, Query

from backend.controllers.beetle_controller import (
    get_beetle_by_id_controller,
    get_environment_ranges_controller,
    get_beetle_media_controller,
    get_country_detail_controller,
    get_featured_beetles_controller,
    list_beetles_controller,
)
from backend.routers.openapi_examples import (
    BEETLE_DETAIL_EXAMPLE,
    BEETLE_MEDIA_EXAMPLE,
    BEETLES_LIST_EXAMPLE,
    COUNTRY_DETAIL_EXAMPLE,
)
from backend.config.query_params import beetle_query_params


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
    """Gibt eine paginierte Kaefer-Liste fuer die angegebenen Query-/Filter-Parameter zurueck."""
    return list_beetles_controller(**params)


@router.get(
    "/api/beetles/featured",
    responses={
        200: {
            "description": "Featured beetles with their real backend rec-IDs.",
        }
    },
)
def get_featured_beetles():
    """Gibt die Featured-Kaefer (echte rec-IDs + Name) zurueck; muss VOR der
    dynamischen /{beetle_id}-Route stehen, damit 'featured' nicht als ID gilt."""
    return get_featured_beetles_controller()


@router.get(
    "/api/beetles/ranges/environment",
    responses={
        200: {
            "description": "Global min/max ranges for environmental quicklook metrics.",
        }
    },
)
def get_environment_ranges():
    """Gibt globale Min/Max-Wertebereiche fuer die relative Quicklook-Balken-Skalierung zurueck."""
    return get_environment_ranges_controller()

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
    """Gibt einen einzelnen Kaefer-Eintrag anhand der Beobachtungs-ID zurueck."""
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
    """Gibt paginierte Medien-Eintraege fuer eine Kaefer-Beobachtung zurueck."""
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
    """Gibt aggregierte Kaefer-Zusammenfassungsinformationen fuer einen Laendercode zurueck."""
    return get_country_detail_controller(country_code)
