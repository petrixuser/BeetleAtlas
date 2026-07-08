"""API-Router fuer schreibende Kaefer-Endpunkte:
Anlegen, Aktualisieren und Loeschen manueller Kaefer-Datensaetze."""

from fastapi import APIRouter, Depends

from backend.controllers.beetle_write_controller import (
    create_beetle_record_controller,
    delete_beetle_record_controller,
    update_beetle_record_controller,
)
from backend.contracts.auth_contracts import AuthUserResponse
from backend.contracts.beetle_write_contracts import (
    BeetleCreateRequest,
    BeetleRecordResponse,
    BeetleUpdateRequest,
)
from backend.core.auth import require_roles


router = APIRouter()


@router.post("/api/beetles", response_model=BeetleRecordResponse)
def create_beetle_record(
    payload: BeetleCreateRequest,
    current_user: AuthUserResponse = Depends(require_roles("researcher", "admin")),
):
    """Legt einen manuellen Kaefer-Eintrag als Researcher/Admin an."""
    return create_beetle_record_controller(payload=payload, current_user=current_user)


@router.patch("/api/beetles/{record_id}", response_model=BeetleRecordResponse)
def update_beetle_record(
    record_id: int,
    payload: BeetleUpdateRequest,
    current_user: AuthUserResponse = Depends(require_roles("researcher", "admin")),
):
    """Aktualisiert einen manuellen Kaefer-Eintrag als Admin oder als dessen Ersteller."""
    return update_beetle_record_controller(record_id=record_id, payload=payload, current_user=current_user)


@router.delete("/api/beetles/{record_id}")
def delete_beetle_record(
    record_id: int,
    current_user: AuthUserResponse = Depends(require_roles("admin")),
):
    """Soft-Delete eines manuellen Kaefer-Eintrags als Admin."""
    return delete_beetle_record_controller(record_id=record_id, current_user=current_user)
