"""SQL-Bausteine fuer den Schreib-Pfad (Core-Wiederverwendung von Art/Ort).

Enthaelt die Feldgruppen (welche Spalten wohin gehoeren) und die SQL-Builder
fuer beetle_record_core, beetle_species, location, climate_snapshot und Medien.
"""

from backend.config.beetle_field_groups import (
    BEETLE_RECORD_CORE_FIELDS,
    BEETLE_RECORD_LOCATION_FIELDS,
    BEETLE_RECORD_MEDIA_FIELDS,
)


def species_find_by_name_sql() -> str:
    """Liefert das SELECT-SQL, das eine Art in beetle_species per scientific_name findet."""
    return """
        SELECT beetle_id
        FROM beetle_species
        WHERE scientific_name = :scientific_name
        ORDER BY beetle_id
        LIMIT 1
    """


def species_next_id_sql() -> str:
    """Liefert das SQL fuer die naechste freie beetle_id in beetle_species."""
    return "SELECT COALESCE(MAX(beetle_id), 0) + 1 AS next_id FROM beetle_species"


def species_insert_sql() -> str:
    """Liefert das INSERT-SQL fuer eine neue Art in beetle_species."""
    return """
        INSERT INTO beetle_species (
            beetle_id, taxon_id, family, genus, specific_epithet,
            scientific_name, scientific_name_authorship
        )
        VALUES (
            :beetle_id, :taxon_id, :family, :genus, :specific_epithet,
            :scientific_name, :scientific_name_authorship
        )
    """


def location_find_by_coords_sql() -> str:
    """Liefert das SELECT-SQL, das einen Ort in location per latitude/longitude findet."""
    return """
        SELECT location_id
        FROM location
        WHERE latitude = :latitude AND longitude = :longitude
        ORDER BY location_id
        LIMIT 1
    """


def location_next_id_sql() -> str:
    """Liefert das SQL fuer die naechste freie location_id in location."""
    return "SELECT COALESCE(MAX(location_id), 0) + 1 AS next_id FROM location"


def location_insert_sql() -> str:
    """Liefert das INSERT-SQL fuer einen neuen Ort in location (inkl. statischer Umweltfelder)."""
    columns_sql = ",\n            ".join(BEETLE_RECORD_LOCATION_FIELDS)
    placeholders_sql = ",\n            ".join(f":{f}" for f in BEETLE_RECORD_LOCATION_FIELDS)
    return f"""
        INSERT INTO location (
            location_id,
            {columns_sql}
        )
        VALUES (
            :location_id,
            {placeholders_sql}
        )
    """


def location_update_sql(fields) -> str:
    """Liefert das UPDATE-SQL fuer einen Ort in location fuer die uebergebenen Felder."""
    set_sql = ",\n            ".join(f"{f} = :{f}" for f in fields)
    return f"""
        UPDATE location
        SET
            {set_sql}
        WHERE location_id = :location_id
    """


def climate_snapshot_upsert_sql() -> str:
    """Liefert das upsert-SQL fuer die dynamische Umwelt in climate_snapshot."""
    # Payload 'temperature' -> Spalte avg_temperature.
    return """
        INSERT INTO climate_snapshot (
            location_id, snapshot_date, avg_temperature, precipitation, soil_moisture,
            ndvi, relative_humidity, surface_pressure_hpa, nighttime_lights
        )
        VALUES (
            :location_id, :snapshot_date, :temperature, :precipitation, :soil_moisture,
            :ndvi, :relative_humidity, :surface_pressure_hpa, :nighttime_lights
        )
        ON DUPLICATE KEY UPDATE
            avg_temperature = VALUES(avg_temperature),
            precipitation = VALUES(precipitation),
            soil_moisture = VALUES(soil_moisture),
            ndvi = VALUES(ndvi),
            relative_humidity = VALUES(relative_humidity),
            surface_pressure_hpa = VALUES(surface_pressure_hpa),
            nighttime_lights = VALUES(nighttime_lights)
    """


def beetle_record_core_insert_sql() -> str:
    """Liefert das INSERT-SQL fuer einen neuen Kerneintrag in beetle_record_core."""
    columns_sql = ",\n            ".join(BEETLE_RECORD_CORE_FIELDS)
    placeholders_sql = ",\n            ".join(f":{f}" for f in BEETLE_RECORD_CORE_FIELDS)
    return f"""
        INSERT INTO beetle_record_core (
            beetle_id,
            location_id,
            {columns_sql},
            status,
            created_by,
            updated_by,
            deleted_by,
            deleted_at
        )
        VALUES (
            :beetle_id,
            :location_id,
            {placeholders_sql},
            'active',
            :created_by,
            NULL,
            NULL,
            NULL
        )
    """


def beetle_record_media_insert_sql() -> str:
    """INSERT eines Medieneintrags (1:N; media_id ist AUTO_INCREMENT)."""
    columns_sql = ",\n            ".join(BEETLE_RECORD_MEDIA_FIELDS)
    placeholders_sql = ",\n            ".join(f":{f}" for f in BEETLE_RECORD_MEDIA_FIELDS)
    return f"""
        INSERT INTO beetle_record_media (
            record_id,
            {columns_sql}
        )
        VALUES (
            :record_id,
            {placeholders_sql}
        )
    """


def beetle_record_media_delete_by_record_sql() -> str:
    """Loescht alle Medien eines manuellen Kaefers (fuer Ersetzen beim Update)."""
    return "DELETE FROM beetle_record_media WHERE record_id = :record_id"


def beetle_record_media_list_sql() -> str:
    """Alle Medien eines manuellen Kaefers (fuer den Medien-Endpunkt)."""
    columns_sql = ",\n            ".join(BEETLE_RECORD_MEDIA_FIELDS)
    return f"""
        SELECT
            media_id,
            {columns_sql}
        FROM beetle_record_media
        WHERE record_id = :record_id
        ORDER BY media_id
    """


def beetle_record_core_update_sql(set_sql: str) -> str:
    """Liefert das UPDATE-SQL fuer einen aktiven Kerneintrag in beetle_record_core."""
    return f"""
        UPDATE beetle_record_core
        SET
            {set_sql}
        WHERE record_id = :record_id
          AND status = 'active'
    """


def beetle_record_soft_delete_sql() -> str:
    """Liefert das UPDATE-SQL fuer das Soft-Delete eines Kaefers (status -> 'deleted')."""
    return """
        UPDATE beetle_record_core
        SET
            status = 'deleted',
            deleted_by = :deleted_by,
            deleted_at = :deleted_at,
            updated_by = :deleted_by
        WHERE record_id = :record_id
          AND status = 'active'
    """


def beetle_record_core_by_id_sql() -> str:
    """Liefert das SELECT-SQL fuer einen Kerneintrag per record_id."""
    return """
        SELECT record_id, beetle_id, location_id, status
        FROM beetle_record_core
        WHERE record_id = :record_id
        LIMIT 1
    """


def beetle_record_audit_insert_sql() -> str:
    """Liefert das INSERT-SQL fuer einen Audit-Eintrag in beetle_record_audit."""
    return """
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


def beetle_record_by_id_sql() -> str:
    """Liefert das SELECT-SQL fuer einen Kaefer per record_id ueber die flache View beetle_record."""
    return """
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


def beetle_record_by_gbif_id_sql() -> str:
    """Liefert das SELECT-SQL fuer einen Kaefer per gbif_id ueber die flache View beetle_record."""
    return """
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
