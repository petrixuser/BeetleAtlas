BEETLE_RECORD_MUTABLE_FIELDS = (
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
)


BEETLE_RECORD_INSERT_FIELDS = BEETLE_RECORD_MUTABLE_FIELDS


BEETLE_RECORD_EE_FIELDS = (
    "elevation",
    "temperature",
    "precipitation",
    "soil_moisture",
    "ndvi",
    "relative_humidity",
    "surface_pressure_hpa",
    "nighttime_lights",
    "slope",
    "distance_to_water_m",
    "human_modification",
    "landcover_class",
    "ecoregion_id",
    "biome_id",
    "soil_ph",
    "soil_organic_carbon",
    "worldclim_bio01",
    "worldclim_bio12",
)


def beetle_record_audit_insert_sql() -> str:
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


def beetle_record_insert_sql() -> str:
    columns_sql = ",\n            ".join(BEETLE_RECORD_INSERT_FIELDS)
    placeholders_sql = ",\n            ".join(f":{field}" for field in BEETLE_RECORD_INSERT_FIELDS)
    return f"""
        INSERT INTO beetle_record (
            {columns_sql},
            status,
            created_by,
            updated_by,
            deleted_by,
            deleted_at
        )
        VALUES (
            {placeholders_sql},
            'active',
            :created_by,
            NULL,
            NULL,
            NULL
        )
    """


def beetle_record_update_active_sql(set_sql: str) -> str:
    return f"""
        UPDATE beetle_record
        SET
            {set_sql}
        WHERE record_id = :record_id
          AND status = 'active'
    """


def beetle_record_soft_delete_sql() -> str:
    return """
        UPDATE beetle_record
        SET
            status = 'deleted',
            deleted_by = :deleted_by,
            deleted_at = :deleted_at,
            updated_by = :deleted_by
        WHERE record_id = :record_id
          AND status = 'active'
    """
