import json
from datetime import datetime, timezone

from sqlalchemy import text

from backend.config.beetle_write_repository_sql import (
    BEETLE_RECORD_EE_FIELDS,
    BEETLE_RECORD_INSERT_FIELDS,
    BEETLE_RECORD_MUTABLE_FIELDS,
    beetle_record_audit_insert_sql,
    beetle_record_by_gbif_id_sql,
    beetle_record_by_id_sql,
    beetle_record_insert_sql,
    beetle_record_soft_delete_sql,
    beetle_record_update_active_sql,
)
from backend.core.db import get_connection


def insert_beetle_record_audit(
    record_id: int,
    action: str,
    actor_user_id: int,
    old_values: dict | None,
    new_values: dict | None,
):
    """Insert one audit-log entry for a beetle_record mutation."""
    sql = text(beetle_record_audit_insert_sql())

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
    sql = text(beetle_record_by_id_sql())

    with get_connection() as conn:
        row = conn.execute(sql, {"record_id": record_id}).mappings().first()

    return dict(row) if row is not None else None


def fetch_beetle_record_by_gbif_id(gbif_id: int):
    """Fetch one beetle_record row by GBIF occurrence id."""
    sql = text(beetle_record_by_gbif_id_sql())

    with get_connection() as conn:
        row = conn.execute(sql, {"gbif_id": gbif_id}).mappings().first()

    return dict(row) if row is not None else None


def insert_beetle_record(payload: dict, created_by: int):
    """Insert one beetle_record row and return it."""
    sql = text(beetle_record_insert_sql())

    params = {field: payload.get(field) for field in BEETLE_RECORD_INSERT_FIELDS}
    params["created_by"] = created_by

    with get_connection() as conn:
        result = conn.execute(sql, params)
        conn.commit()
        created_id = int(result.lastrowid)

    return fetch_beetle_record_by_id(created_id)


def update_beetle_record(record_id: int, payload: dict, updated_by: int):
    """Apply partial update to an active beetle_record row."""
    set_clauses = []
    params = {"record_id": record_id, "updated_by": updated_by}

    for key in BEETLE_RECORD_MUTABLE_FIELDS:
        if key in payload and payload[key] is not None:
            set_clauses.append(f"{key} = :{key}")
            params[key] = payload[key]

    if not set_clauses:
        return fetch_beetle_record_by_id(record_id)

    set_sql = ",\n            ".join(set_clauses + ["updated_by = :updated_by"])

    sql = text(beetle_record_update_active_sql(set_sql))

    with get_connection() as conn:
        conn.execute(sql, params)
        conn.commit()

    return fetch_beetle_record_by_id(record_id)


def soft_delete_beetle_record(record_id: int, deleted_by: int):
    """Soft delete one active beetle_record row and return updated row."""
    now_utc = datetime.now(timezone.utc).replace(tzinfo=None)
    sql = text(beetle_record_soft_delete_sql())

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


def update_beetle_record_ee_fields(record_id: int, ee_payload: dict, updated_by: int | None = None):
    """Update EE/environment fields for one active manual beetle record.

    This helper is intended for internal enrichment jobs, not direct API input.
    """
    set_clauses = []
    params: dict[str, object | None] = {"record_id": record_id}

    for key in BEETLE_RECORD_EE_FIELDS:
        if key in ee_payload:
            set_clauses.append(f"{key} = :{key}")
            params[key] = ee_payload.get(key)

    if updated_by is not None:
        set_clauses.append("updated_by = :updated_by")
        params["updated_by"] = updated_by

    if not set_clauses:
        return fetch_beetle_record_by_id(record_id)

    set_sql = ",\n            ".join(set_clauses)
    sql = text(beetle_record_update_active_sql(set_sql))

    with get_connection() as conn:
        conn.execute(sql, params)
        conn.commit()

    return fetch_beetle_record_by_id(record_id)
