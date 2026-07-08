"""Schreib-Repository fuer manuelle Kaefer-Datensaetze.

Schreibt in die normalisierten Tabellen (beetle_record_core, beetle_species,
location, climate_snapshot, beetle_record_media) und wendet die
Core-Wiederverwendung an: Arten und Orte werden nur einmal gespeichert.
"""
import json
import logging
from datetime import date, datetime, timezone

from sqlalchemy import text

from backend.config.beetle_field_groups import (
    BEETLE_RECORD_CLIMATE_FIELDS,
    BEETLE_RECORD_CORE_FIELDS,
    BEETLE_RECORD_EE_FIELDS,
    BEETLE_RECORD_LOCATION_FIELDS,
    BEETLE_RECORD_MEDIA_FIELDS,
    BEETLE_RECORD_MUTABLE_FIELDS,
    BEETLE_RECORD_SPECIES_FIELDS,
)
from backend.config.sql.beetle_write_repository_sql import (
    beetle_record_audit_insert_sql,
    beetle_record_by_gbif_id_sql,
    beetle_record_by_id_sql,
    beetle_record_core_by_id_sql,
    beetle_record_core_insert_sql,
    beetle_record_core_update_sql,
    beetle_record_media_delete_by_record_sql,
    beetle_record_media_insert_sql,
    beetle_record_media_list_sql,
    beetle_record_soft_delete_sql,
    climate_snapshot_upsert_sql,
    location_find_by_coords_sql,
    location_insert_sql,
    location_next_id_sql,
    location_update_sql,
    species_find_by_name_sql,
    species_insert_sql,
    species_next_id_sql,
)
from backend.core.db import get_connection


def refresh_read_models_for_record(record_id: int) -> None:
    """Aktualisiert die vorberechneten Read-Modelle (map_point_read und
    beetle_list_read) inkrementell fuer einen manuellen Kaefer, damit der Schreibvorgang
    sofort auf der Karte und in der kompakten Liste erscheint statt erst nach dem
    naechsten vollstaendigen Rebuild."""
    try:
        with get_connection() as conn:
            conn.execute(
                text("CALL refresh_read_models_for_record(:record_id)"),
                {"record_id": record_id},
            )
            conn.commit()
    except Exception:
        logging.getLogger(__name__).warning(
            "refresh_read_models_for_record failed for record_id=%s; "
            "map/compact list may be stale until the next full refresh",
            record_id,
            exc_info=True,
        )


def invalidate_read_caches() -> None:
    """Verwirft die In-Memory-Antwort-Caches nach einem manuellen Kaefer-Schreibvorgang."""
    try:
        from backend.controllers.map_controller import clear_map_response_cache
        from backend.controllers.beetle_controller import clear_read_caches

        clear_map_response_cache()
        clear_read_caches()
    except Exception:
        logging.getLogger(__name__).warning(
            "invalidate_read_caches failed; map/country/list caches may be stale "
            "until the backend restarts",
            exc_info=True,
        )


def insert_beetle_record_audit(
    record_id: int,
    action: str,
    actor_user_id: int,
    old_values: dict | None,
    new_values: dict | None,
):
    """Fuegt einen Audit-Log-Eintrag fuer eine Mutation an beetle_record ein."""
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
    """Laedt einen manuellen Kaefer (flache View) anhand der record_id."""
    sql = text(beetle_record_by_id_sql())

    with get_connection() as conn:
        row = conn.execute(sql, {"record_id": record_id}).mappings().first()

    return dict(row) if row is not None else None


def fetch_beetle_record_by_gbif_id(gbif_id: int):
    """Laedt einen manuellen Kaefer anhand der gbif_id (GBIF-Occurrence)."""
    sql = text(beetle_record_by_gbif_id_sql())

    with get_connection() as conn:
        row = conn.execute(sql, {"gbif_id": gbif_id}).mappings().first()

    return dict(row) if row is not None else None


def fetch_beetle_record_media_rows(record_id: int) -> list[dict]:
    """Alle Medien eines manuellen Kaefers (1:N), sortiert nach media_id."""
    with get_connection() as conn:
        rows = conn.execute(
            text(beetle_record_media_list_sql()), {"record_id": record_id}
        ).mappings().all()
    return [dict(r) for r in rows]


def _media_row_params(record_id: int, item: dict) -> dict:
    """Baut die Insert-Parameter fuer eine Medienzeile; image_available wird aus
    der URL abgeleitet, falls nicht gesetzt (erfuellt die CHECK-Constraint)."""
    url = item.get("image_url")
    available = item.get("image_available")
    if available is None:
        available = 1 if (url and str(url).strip()) else None
    return {
        "record_id": record_id,
        "image_available": available,
        "image_url": url,
        "media_references": item.get("media_references"),
        "media_creator": item.get("media_creator"),
        "media_publisher": item.get("media_publisher"),
        "media_rights_holder": item.get("media_rights_holder"),
        "media_license": item.get("media_license"),
    }


def _media_items_from_payload(payload: dict) -> list[dict]:
    """Liefert die Medienliste: entweder aus payload['media_items'] (Mehrbild)
    oder aus den Einzel-Bildfeldern (Rueckwaerts-Kompatibilitaet)."""
    items = payload.get("media_items")
    if items:
        return [
            dict(it)
            for it in items
            if isinstance(it, dict) and it.get("image_url") and str(it.get("image_url")).strip()
        ]
    url = payload.get("image_url")
    if url and str(url).strip():
        return [{
            "image_url": url,
            "image_available": payload.get("image_available"),
            "media_references": payload.get("media_references"),
            "media_creator": payload.get("media_creator"),
            "media_publisher": payload.get("media_publisher"),
            "media_rights_holder": payload.get("media_rights_holder"),
            "media_license": payload.get("media_license"),
        }]
    return []


def _insert_media_items(conn, record_id: int, items: list[dict]) -> None:
    """Fuegt alle uebergebenen Medienzeilen fuer einen manuellen Kaefer ein."""
    for item in items:
        conn.execute(text(beetle_record_media_insert_sql()), _media_row_params(record_id, item))


def _payload_touches_media(payload: dict) -> bool:
    """Prueft, ob das Payload Medienfelder (media_items oder Einzelfelder) betrifft."""
    return "media_items" in payload or any(
        payload.get(f) is not None for f in BEETLE_RECORD_MEDIA_FIELDS
    )


# --- Core-Wiederverwendung: Art/Ort finden oder anlegen ----------------------
def _resolve_species_id(conn, payload: dict) -> int:
    """Verwendet eine vorhandene Art per scientific_name wieder, sonst wird eine
    neue angelegt (beetle_id = MAX+1). So wird dieselbe Art nur einmal gespeichert."""
    name = payload.get("scientific_name")
    if name:
        row = conn.execute(text(species_find_by_name_sql()), {"scientific_name": name}).first()
        if row is not None:
            return int(row[0])
    new_id = int(conn.execute(text(species_next_id_sql())).scalar_one())
    conn.execute(
        text(species_insert_sql()),
        {"beetle_id": new_id, **{f: payload.get(f) for f in BEETLE_RECORD_SPECIES_FIELDS}},
    )
    return new_id


def _resolve_location_id(conn, payload: dict) -> tuple[int | None, bool]:
    """Verwendet einen vorhandenen Ort per exakter Koordinaten wieder, sonst wird ein
    neuer angelegt (location_id = MAX+1). Ohne Koordinaten wird KEIN Ort angelegt -> (None, False),
    der Kaefer ist trotzdem anlegbar (erscheint dann nur nicht auf der Karte).
    Gibt (location_id | None, created_new) zurueck."""
    lat = payload.get("latitude")
    lng = payload.get("longitude")
    if lat is None or lng is None:
        return None, False
    row = conn.execute(
        text(location_find_by_coords_sql()), {"latitude": lat, "longitude": lng}
    ).first()
    if row is not None:
        return int(row[0]), False
    new_id = int(conn.execute(text(location_next_id_sql())).scalar_one())
    conn.execute(
        text(location_insert_sql()),
        {"location_id": new_id, **{f: payload.get(f) for f in BEETLE_RECORD_LOCATION_FIELDS}},
    )
    return new_id, True


def _write_climate_snapshot(conn, location_id: int, payload: dict) -> None:
    """Upsert einer climate_snapshot-Zeile (heute), falls ein dynamischer Umweltwert vorliegt."""
    if not any(payload.get(f) is not None for f in BEETLE_RECORD_CLIMATE_FIELDS):
        return
    conn.execute(
        text(climate_snapshot_upsert_sql()),
        {
            "location_id": location_id,
            "snapshot_date": date.today(),
            **{f: payload.get(f) for f in BEETLE_RECORD_CLIMATE_FIELDS},
        },
    )


def _update_location_fields(conn, location_id: int, values: dict) -> None:
    """Aktualisiert die uebergebenen Felder einer location-Zeile (No-op ohne Werte)."""
    if not values:
        return
    conn.execute(
        text(location_update_sql(values.keys())),
        {"location_id": location_id, **values},
    )


def insert_beetle_record(payload: dict, created_by: int):
    """Legt einen manuellen Kaefer an: Art + Ort wiederverwenden/erstellen (ohne Duplikate),
    optional einen climate_snapshot, danach die beetle_record_core-Zeile + Medien."""
    with get_connection() as conn:
        beetle_id = _resolve_species_id(conn, payload)
        location_id, loc_is_new = _resolve_location_id(conn, payload)
        if loc_is_new and location_id is not None:
            _write_climate_snapshot(conn, location_id, payload)

        core_params = {
            "beetle_id": beetle_id,
            "location_id": location_id,
            "created_by": created_by,
            **{field: payload.get(field) for field in BEETLE_RECORD_CORE_FIELDS},
        }
        result = conn.execute(text(beetle_record_core_insert_sql()), core_params)
        created_id = int(result.lastrowid)

        _insert_media_items(conn, created_id, _media_items_from_payload(payload))
        conn.commit()

    refresh_read_models_for_record(created_id)
    invalidate_read_caches()
    return fetch_beetle_record_by_id(created_id)


def update_beetle_record(record_id: int, payload: dict, updated_by: int):
    """Wendet ein Teil-Update auf einen aktiven manuellen Kaefer an."""
    with get_connection() as conn:
        current = conn.execute(
            text(beetle_record_core_by_id_sql()), {"record_id": record_id}
        ).mappings().first()
        if current is None or current["status"] != "active":
            return fetch_beetle_record_by_id(record_id)
        location_id = current["location_id"]
        location_id = int(location_id) if location_id is not None else None

        core_set: dict[str, object | None] = {}
        if payload.get("scientific_name"):
            core_set["beetle_id"] = _resolve_species_id(conn, payload)

        # Koordinaten im Patch -> Ort (neu) aufloesen und FK setzen.
        if payload.get("latitude") is not None and payload.get("longitude") is not None:
            new_loc_id, _ = _resolve_location_id(conn, payload)
            if new_loc_id is not None:
                core_set["location_id"] = new_loc_id
                location_id = new_loc_id

        if location_id is not None:
            _update_location_fields(
                conn,
                location_id,
                {f: payload[f] for f in BEETLE_RECORD_LOCATION_FIELDS if f in payload and payload[f] is not None},
            )
            _write_climate_snapshot(conn, location_id, payload)

        core_set.update(
            {f: payload[f] for f in BEETLE_RECORD_CORE_FIELDS if f in payload and payload[f] is not None}
        )
        set_clauses = [f"{k} = :{k}" for k in core_set] + ["updated_by = :updated_by"]
        conn.execute(
            text(beetle_record_core_update_sql(",\n            ".join(set_clauses))),
            {"record_id": record_id, "updated_by": updated_by, **core_set},
        )

        # Medien (1:N): bei Aenderung komplett ersetzen.
        if _payload_touches_media(payload):
            conn.execute(text(beetle_record_media_delete_by_record_sql()), {"record_id": record_id})
            _insert_media_items(conn, record_id, _media_items_from_payload(payload))
        conn.commit()

    refresh_read_models_for_record(record_id)
    invalidate_read_caches()
    return fetch_beetle_record_by_id(record_id)


def soft_delete_beetle_record(record_id: int, deleted_by: int):
    """Setzt einen aktiven manuellen Kaefer per Soft-Delete und gibt die aktualisierte Zeile zurueck."""
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

    refresh_read_models_for_record(record_id)
    invalidate_read_caches()
    return fetch_beetle_record_by_id(record_id)


def update_beetle_record_ee_fields(record_id: int, ee_payload: dict, updated_by: int | None = None):
    """Aktualisiert EE-/Umweltfelder eines aktiven manuellen Kaefers. """
    with get_connection() as conn:
        current = conn.execute(
            text(beetle_record_core_by_id_sql()), {"record_id": record_id}
        ).mappings().first()
        if current is None or current["status"] != "active":
            return fetch_beetle_record_by_id(record_id)
        location_id = current["location_id"]
        if location_id is None:
            return fetch_beetle_record_by_id(record_id)
        location_id = int(location_id)

        _update_location_fields(
            conn,
            location_id,
            {f: ee_payload[f] for f in BEETLE_RECORD_LOCATION_FIELDS if f in ee_payload},
        )
        _write_climate_snapshot(conn, location_id, ee_payload)

        if updated_by is not None:
            conn.execute(
                text(beetle_record_core_update_sql("updated_by = :updated_by")),
                {"record_id": record_id, "updated_by": updated_by},
            )
        conn.commit()

    refresh_read_models_for_record(record_id)
    invalidate_read_caches()
    return fetch_beetle_record_by_id(record_id)
