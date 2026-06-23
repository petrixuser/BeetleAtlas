from backend.contracts.auth_contracts import AuthUserResponse
from backend.contracts.beetle_write_contracts import (
    BeetleCreateRequest,
    BeetleRecordResponse,
    BeetleUpdateRequest,
)
from backend.config.error_codes import ERR
from backend.controllers.core_controller import raise_api_error
from backend.repositories.beetle_write_repository import (
    fetch_beetle_record_by_gbif_id,
    fetch_beetle_record_by_id,
    insert_beetle_record,
    insert_beetle_record_audit,
    soft_delete_beetle_record,
    update_beetle_record,
)


def _to_response(row: dict) -> BeetleRecordResponse:
    return BeetleRecordResponse(
        id=int(row["record_id"]),
        gbif_id=int(row["gbif_id"]) if row.get("gbif_id") is not None else None,
        taxon_id=row.get("taxon_id"),
        scientific_name=row["scientific_name"],
        scientific_name_authorship=row.get("scientific_name_authorship"),
        family=row["family"],
        genus=row.get("genus"),
        specific_epithet=row.get("specific_epithet"),
        recorded_by=row.get("recorded_by"),
        catalogue_number=row.get("catalogue_number"),
        identification_id=row.get("identification_id"),
        identified_by=row.get("identified_by"),
        event_date=row.get("event_date"),
        verbatim_event_date=row.get("verbatim_event_date"),
        basis_of_record=row.get("basis_of_record"),
        dataset_name=row.get("dataset_name"),
        institution_code=row.get("institution_code"),
        image_available=bool(row["image_available"]) if row.get("image_available") is not None else None,
        image_url=row.get("image_url"),
        media_references=row.get("media_references"),
        media_creator=row.get("media_creator"),
        media_publisher=row.get("media_publisher"),
        media_rights_holder=row.get("media_rights_holder"),
        media_license=row.get("media_license"),
        latitude=float(row["latitude"]) if row.get("latitude") is not None else None,
        longitude=float(row["longitude"]) if row.get("longitude") is not None else None,
        coordinate_uncertainty=row.get("coordinate_uncertainty"),
        country=row.get("country"),
        region=row.get("region"),
        city=row.get("city"),
        verbatim_locality=row.get("verbatim_locality"),
        location=row.get("location"),
        notes=row.get("notes"),
        status=row["status"],
        created_by=int(row["created_by"]),
        updated_by=int(row["updated_by"]) if row.get("updated_by") is not None else None,
        deleted_by=int(row["deleted_by"]) if row.get("deleted_by") is not None else None,
        created_at=row["created_at"],
        updated_at=row["updated_at"],
        deleted_at=row.get("deleted_at"),
    )


def _validate_gbif_assignment_or_error(
    *,
    gbif_id: int | None,
    current_user: AuthUserResponse,
    current_record_id: int | None = None,
) -> None:
    """Validate role and uniqueness constraints for assigning gbif_id."""
    if gbif_id is None:
        return

    if current_user.role == "researcher":
        raise_api_error(
            403,
            ERR.COMMON.FORBIDDEN,
            "Researchers are not allowed to set gbif_id.",
        )

    existing_by_gbif = fetch_beetle_record_by_gbif_id(int(gbif_id))
    if existing_by_gbif is None:
        return

    if current_record_id is not None and int(existing_by_gbif["record_id"]) == int(current_record_id):
        return

    raise_api_error(409, ERR.BEETLE_WRITE.GBIF_ID_EXISTS, "A beetle record with this GBIF ID already exists.")


def create_beetle_record_controller(payload: BeetleCreateRequest, current_user: AuthUserResponse) -> BeetleRecordResponse:
    """Create one manual beetle record for researcher/admin."""
    _validate_gbif_assignment_or_error(gbif_id=payload.gbif_id, current_user=current_user)

    row = insert_beetle_record(payload.model_dump(), created_by=current_user.id)
    if row is None:
        raise_api_error(500, ERR.BEETLE_WRITE.CREATE_FAILED, "Could not create beetle record.")

    insert_beetle_record_audit(
        record_id=int(row["record_id"]),
        action="create",
        actor_user_id=current_user.id,
        old_values=None,
        new_values=row,
    )

    return _to_response(row)


def update_beetle_record_controller(
    record_id: int,
    payload: BeetleUpdateRequest,
    current_user: AuthUserResponse,
) -> BeetleRecordResponse:
    """Patch one active beetle record as admin or as its creator."""
    existing = fetch_beetle_record_by_id(record_id)
    if existing is None or existing.get("status") == "deleted":
        raise_api_error(404, ERR.COMMON.NOT_FOUND, "Beetle record not found.")

    created_by = int(existing.get("created_by") or 0)
    if current_user.role != "admin" and current_user.id != created_by:
        raise_api_error(403, ERR.COMMON.FORBIDDEN, "Insufficient permissions.")

    patch_payload = payload.model_dump(exclude_unset=True)
    _validate_gbif_assignment_or_error(
        gbif_id=patch_payload.get("gbif_id"),
        current_user=current_user,
        current_record_id=record_id,
    )

    updated = update_beetle_record(record_id, patch_payload, updated_by=current_user.id)
    if updated is None:
        raise_api_error(404, ERR.COMMON.NOT_FOUND, "Beetle record not found.")

    insert_beetle_record_audit(
        record_id=record_id,
        action="update",
        actor_user_id=current_user.id,
        old_values=existing,
        new_values={**updated, "patched_fields": patch_payload},
    )

    return _to_response(updated)


def delete_beetle_record_controller(record_id: int, current_user: AuthUserResponse) -> dict:
    """Soft delete one active beetle record (admin only at router level)."""
    existing = fetch_beetle_record_by_id(record_id)
    if existing is None or existing.get("status") == "deleted":
        raise_api_error(404, ERR.COMMON.NOT_FOUND, "Beetle record not found.")

    deleted = soft_delete_beetle_record(record_id, deleted_by=current_user.id)
    if deleted is None:
        raise_api_error(404, ERR.COMMON.NOT_FOUND, "Beetle record not found.")

    insert_beetle_record_audit(
        record_id=record_id,
        action="delete",
        actor_user_id=current_user.id,
        old_values=existing,
        new_values=deleted,
    )

    return {"status": "deleted", "id": int(deleted["record_id"]) }
