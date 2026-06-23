import json
from datetime import datetime, timezone

from sqlalchemy import text

from backend.core.db import get_connection


def insert_beetle_record_audit(
    record_id: int,
    action: str,
    actor_user_id: int,
    old_values: dict | None,
    new_values: dict | None,
):
    """Insert one audit-log entry for a beetle_record mutation."""
    sql = text(
        """
        INSERT INTO beetle_record_audit (
            record_id,
            action,
            actor_user_id,
            old_values,
            new_values
        )
        VALUES (
            :record_id,
            :action,
            :actor_user_id,
            :old_values,
            :new_values
        )
        """
    )

    with get_connection() as conn:
        conn.execute(
            sql,
            {
                "record_id": record_id,
                "action": action,
                "actor_user_id": actor_user_id,
                "old_values": None if old_values is None else json.dumps(old_values, default=str),
                "new_values": None if new_values is None else json.dumps(new_values, default=str),
            },
        )
        conn.commit()


def fetch_beetle_record_by_id(record_id: int):
    """Fetch one beetle_record row by ID."""
    sql = text(
        """
        SELECT
            record_id,
            gbif_id,
            taxon_id,
            scientific_name,
            scientific_name_authorship,
            family,
            genus,
            specific_epithet,
            recorded_by,
            catalogue_number,
            identification_id,
            identified_by,
            event_date,
            verbatim_event_date,
            basis_of_record,
            dataset_name,
            institution_code,
            image_available,
            image_url,
            media_references,
            media_creator,
            media_publisher,
            media_rights_holder,
            media_license,
            latitude,
            longitude,
            coordinate_uncertainty,
            country,
            region,
            city,
            verbatim_locality,
            location,
            notes,
            status,
            created_by,
            updated_by,
            deleted_by,
            created_at,
            updated_at,
            deleted_at
        FROM beetle_record
        WHERE record_id = :record_id
        LIMIT 1
        """
    )

    with get_connection() as conn:
        row = conn.execute(sql, {"record_id": record_id}).mappings().first()

    return dict(row) if row is not None else None


def fetch_beetle_record_by_gbif_id(gbif_id: int):
    """Fetch one beetle_record row by GBIF occurrence id."""
    sql = text(
        """
        SELECT
            record_id,
            gbif_id,
            status,
            created_by,
            updated_by,
            deleted_by,
            created_at,
            updated_at,
            deleted_at
        FROM beetle_record
        WHERE gbif_id = :gbif_id
        LIMIT 1
        """
    )

    with get_connection() as conn:
        row = conn.execute(sql, {"gbif_id": gbif_id}).mappings().first()

    return dict(row) if row is not None else None


def insert_beetle_record(payload: dict, created_by: int):
    """Insert one beetle_record row and return it."""
    sql = text(
        """
        INSERT INTO beetle_record (
            gbif_id,
            taxon_id,
            scientific_name,
            scientific_name_authorship,
            family,
            genus,
            specific_epithet,
            recorded_by,
            catalogue_number,
            identification_id,
            identified_by,
            event_date,
            verbatim_event_date,
            basis_of_record,
            dataset_name,
            institution_code,
            image_available,
            image_url,
            media_references,
            media_creator,
            media_publisher,
            media_rights_holder,
            media_license,
            latitude,
            longitude,
            coordinate_uncertainty,
            country,
            region,
            city,
            verbatim_locality,
            location,
            notes,
            status,
            created_by,
            updated_by,
            deleted_by,
            deleted_at
        )
        VALUES (
            :gbif_id,
            :taxon_id,
            :scientific_name,
            :scientific_name_authorship,
            :family,
            :genus,
            :specific_epithet,
            :recorded_by,
            :catalogue_number,
            :identification_id,
            :identified_by,
            :event_date,
            :verbatim_event_date,
            :basis_of_record,
            :dataset_name,
            :institution_code,
            :image_available,
            :image_url,
            :media_references,
            :media_creator,
            :media_publisher,
            :media_rights_holder,
            :media_license,
            :latitude,
            :longitude,
            :coordinate_uncertainty,
            :country,
            :region,
            :city,
            :verbatim_locality,
            :location,
            :notes,
            'active',
            :created_by,
            NULL,
            NULL,
            NULL
        )
        """
    )

    params = {
        "gbif_id": payload.get("gbif_id"),
        "taxon_id": payload.get("taxon_id"),
        "scientific_name": payload.get("scientific_name"),
        "scientific_name_authorship": payload.get("scientific_name_authorship"),
        "family": payload.get("family"),
        "genus": payload.get("genus"),
        "specific_epithet": payload.get("specific_epithet"),
        "recorded_by": payload.get("recorded_by"),
        "catalogue_number": payload.get("catalogue_number"),
        "identification_id": payload.get("identification_id"),
        "identified_by": payload.get("identified_by"),
        "event_date": payload.get("event_date"),
        "verbatim_event_date": payload.get("verbatim_event_date"),
        "basis_of_record": payload.get("basis_of_record"),
        "dataset_name": payload.get("dataset_name"),
        "institution_code": payload.get("institution_code"),
        "image_available": payload.get("image_available"),
        "image_url": payload.get("image_url"),
        "media_references": payload.get("media_references"),
        "media_creator": payload.get("media_creator"),
        "media_publisher": payload.get("media_publisher"),
        "media_rights_holder": payload.get("media_rights_holder"),
        "media_license": payload.get("media_license"),
        "latitude": payload.get("latitude"),
        "longitude": payload.get("longitude"),
        "coordinate_uncertainty": payload.get("coordinate_uncertainty"),
        "country": payload.get("country"),
        "region": payload.get("region"),
        "city": payload.get("city"),
        "verbatim_locality": payload.get("verbatim_locality"),
        "location": payload.get("location"),
        "notes": payload.get("notes"),
        "created_by": created_by,
    }

    with get_connection() as conn:
        result = conn.execute(sql, params)
        conn.commit()
        created_id = int(result.lastrowid)

    return fetch_beetle_record_by_id(created_id)


def update_beetle_record(record_id: int, payload: dict, updated_by: int):
    """Apply partial update to an active beetle_record row."""
    set_clauses = []
    params = {"record_id": record_id, "updated_by": updated_by}

    for key in (
        "gbif_id",
        "taxon_id",
        "scientific_name",
        "scientific_name_authorship",
        "family",
        "genus",
        "specific_epithet",
        "recorded_by",
        "catalogue_number",
        "identification_id",
        "identified_by",
        "event_date",
        "verbatim_event_date",
        "basis_of_record",
        "dataset_name",
        "institution_code",
        "image_available",
        "image_url",
        "media_references",
        "media_creator",
        "media_publisher",
        "media_rights_holder",
        "media_license",
        "latitude",
        "longitude",
        "coordinate_uncertainty",
        "country",
        "region",
        "city",
        "verbatim_locality",
        "location",
        "notes",
    ):
        if key in payload and payload[key] is not None:
            set_clauses.append(f"{key} = :{key}")
            params[key] = payload[key]

    if not set_clauses:
        return fetch_beetle_record_by_id(record_id)

    set_sql = ",\n            ".join(set_clauses + ["updated_by = :updated_by"])

    sql = text(
        f"""
        UPDATE beetle_record
        SET
            {set_sql}
        WHERE record_id = :record_id
          AND status = 'active'
        """
    )

    with get_connection() as conn:
        conn.execute(sql, params)
        conn.commit()

    return fetch_beetle_record_by_id(record_id)


def soft_delete_beetle_record(record_id: int, deleted_by: int):
    """Soft delete one active beetle_record row and return updated row."""
    now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
    sql = text(
        """
        UPDATE beetle_record
        SET
            status = 'deleted',
            deleted_by = :deleted_by,
            deleted_at = :deleted_at,
            updated_by = :deleted_by
        WHERE record_id = :record_id
          AND status = 'active'
        """
    )

    with get_connection() as conn:
        conn.execute(
            sql,
            {
                "record_id": record_id,
                "deleted_by": deleted_by,
                "deleted_at": now_utc,
            },
        )
        conn.commit()

    return fetch_beetle_record_by_id(record_id)
