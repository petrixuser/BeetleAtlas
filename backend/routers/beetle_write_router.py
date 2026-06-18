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
    """Create one manual beetle entry as researcher/admin."""
    return create_beetle_record_controller(payload=payload, current_user=current_user)


@router.patch("/api/beetles/{record_id}", response_model=BeetleRecordResponse)
def update_beetle_record(
    record_id: int,
    payload: BeetleUpdateRequest,
    current_user: AuthUserResponse = Depends(require_roles("researcher", "admin")),
):
    """Update one manual beetle entry as admin or as its creator."""
    return update_beetle_record_controller(record_id=record_id, payload=payload, current_user=current_user)


@router.delete("/api/beetles/{record_id}")
def delete_beetle_record(
    record_id: int,
    current_user: AuthUserResponse = Depends(require_roles("admin")),
):
    """Soft delete one manual beetle entry as admin."""
    return delete_beetle_record_controller(record_id=record_id, current_user=current_user)
