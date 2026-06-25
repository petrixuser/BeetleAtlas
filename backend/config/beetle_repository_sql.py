from backend.config.classifications_sql import (
    BASIS_OF_RECORD_CASE_SQL,
    CLIMATE_CASE_SQL,
    COORDINATE_UNCERTAINTY_BAND_CASE_SQL,
    ELEVATION_GROUP_CASE_SQL,
    EVENT_DATE_QUALITY_CASE_SQL,
    HUMAN_MODIFICATION_BAND_CASE_SQL,
    HUMIDITY_BAND_CASE_SQL,
    LANDCOVER_GROUP_CASE_SQL,
    LICENSE_CLASS_CASE_SQL,
    LIGHT_POLLUTION_BAND_CASE_SQL,
    MEDIA_COVERAGE_CASE_SQL,
    NDVI_BAND_CASE_SQL,
    PRECIPITATION_BAND_CASE_SQL,
    PRESSURE_BAND_CASE_SQL,
    SLOPE_BAND_CASE_SQL,
    SOIL_CARBON_BAND_CASE_SQL,
    SOIL_CASE_SQL,
    SOIL_MOISTURE_BAND_CASE_SQL,
    SOIL_PH_BAND_CASE_SQL,
    TAXON_RESOLUTION_CASE_SQL,
    TEMPERATURE_BAND_CASE_SQL,
    VEGETATION_CASE_SQL,
    WATER_DISTANCE_BAND_CASE_SQL,
    WORLDCLIM_PRECIP_BAND_CASE_SQL,
    WORLCLIM_TEMP_BAND_CASE_SQL,
)


def normalized_soil_ph_sql(location_alias: str = "l") -> str:
    """Return SQL expression that normalizes soil pH sentinel/scaled values."""
    return f"""
                CASE
                    WHEN {location_alias}.soil_ph IS NULL OR {location_alias}.soil_ph = -9999 THEN NULL
                    WHEN {location_alias}.soil_ph > 14 THEN {location_alias}.soil_ph / 10
                    ELSE {location_alias}.soil_ph
                END
    """


def normalized_soil_organic_carbon_sql(location_alias: str = "l") -> str:
    """Return SQL expression that normalizes soil organic carbon values."""
    return f"""
                CASE
                    WHEN {location_alias}.soil_organic_carbon IS NULL OR {location_alias}.soil_organic_carbon = -9999 THEN NULL
                    WHEN {location_alias}.soil_organic_carbon > 60 THEN {location_alias}.soil_organic_carbon / 5
                    ELSE {location_alias}.soil_organic_carbon
                END
    """


def normalized_worldclim_bio01_sql(location_alias: str = "l") -> str:
    """Return SQL expression that normalizes BIO01 temperature values."""
    return f"""
                CASE
                    WHEN {location_alias}.worldclim_bio01 IS NULL OR {location_alias}.worldclim_bio01 = -9999 THEN NULL
                    WHEN {location_alias}.worldclim_bio01 > 80 THEN {location_alias}.worldclim_bio01 / 10
                    ELSE {location_alias}.worldclim_bio01
                END
    """


def event_date_cutoff_sql(observation_alias: str = "o") -> str:
    """Return SQL expression for fallback event-date cutoff used by snapshots."""
    return f"""
COALESCE(
                                                    {observation_alias}.event_date_parsed,
                          STR_TO_DATE(LEFT({observation_alias}.event_date, 10), '%Y-%m-%d'),
                          DATE('9999-12-31')
                      )
    """


def latest_snapshot_join_sql(location_alias: str = "l", observation_alias: str = "o") -> str:
    """Build LEFT JOIN SQL to attach latest climate snapshot at observation time."""
    return f"""
            LEFT JOIN climate_snapshot lc
                ON lc.location_id = {location_alias}.location_id
               AND lc.snapshot_date = (
                    SELECT MAX(cs2.snapshot_date)
                    FROM climate_snapshot cs2
                    WHERE cs2.location_id = {location_alias}.location_id
                      AND cs2.snapshot_date <= {event_date_cutoff_sql(observation_alias)}
               )
    """


def observation_entity_id_sql(observation_alias: str = "o") -> str:
    """Return SQL expression for normalized observation entity IDs."""
    return f"CONCAT('occ-', {observation_alias}.gbif_id)"


def manual_entity_id_sql(record_alias: str = "br") -> str:
    """Return SQL expression for normalized manual-record entity IDs."""
    return f"CONCAT('rec-', {record_alias}.record_id)"


def location_fallback_sql(row_alias: str = "b", include_location_column: bool = False) -> str:
    """Return SQL expression for normalized location display text."""
    location_candidate = f"NULLIF({row_alias}.location, '')," if include_location_column else ""
    return f"""
                COALESCE(
                    {location_candidate}
                    NULLIF({row_alias}.verbatim_locality, ''),
                    NULLIF(CONCAT_WS(', ', {row_alias}.city, {row_alias}.region, {row_alias}.country), ''),
                    NULLIF(CONCAT_WS(', ', {row_alias}.region, {row_alias}.country), ''),
                    {row_alias}.country,
                    'Unbekannt'
                )
    """


def full_enriched_cte_sql(base_where_sql: str, media_where_sql: str = "") -> str:
    """Build full list/detail base+enriched CTE SQL with classifications.

    media_where_sql scopes the media_agg aggregation. For single-row detail
    lookups pass a `WHERE m.gbif_id = :param` so we don't aggregate the entire
    media table (a full scan of millions of rows) just to read one beetle.
    """
    return f"""
        WITH media_agg AS (
            SELECT
                m.gbif_id,
                COUNT(*) AS media_count,
                MIN(m.license) AS license_sample,
                MIN(m.image_url) AS image_url_sample
            FROM media m
            {media_where_sql}
            GROUP BY m.gbif_id
        ),
        base AS (
            SELECT
                'observation' AS source_type,
                NULL AS record_id,
                {observation_entity_id_sql("o")} AS entity_id,
                o.gbif_id,
                o.event_date,
                o.basis_of_record,
                o.dataset_name,
                o.institution_code,
                o.image_available,
                o.taxon_id,
                bs.scientific_name,
                bs.family,
                bs.genus,
                bs.specific_epithet,
                l.latitude,
                l.longitude,
                l.city,
                l.region,
                l.country,
                l.verbatim_locality,
                l.coordinate_uncertainty,
                l.elevation,
                l.landcover_class,
                l.biome_id,
                l.ecoregion_id,
                l.distance_to_water_m,
                l.human_modification,
                l.slope,
                {normalized_soil_ph_sql("l")} AS soil_ph,
                {normalized_soil_organic_carbon_sql("l")} AS soil_organic_carbon,
                {normalized_worldclim_bio01_sql("l")} AS worldclim_bio01,
                l.worldclim_bio12,
                ma.media_count,
                ma.license_sample,
                ma.image_url_sample,
                COALESCE(
                    lc.avg_temperature,
                    {normalized_worldclim_bio01_sql("l")}
                ) AS temperature_value,
                COALESCE(lc.precipitation, l.worldclim_bio12) AS precipitation_value,
                lc.soil_moisture AS soil_moisture_value,
                lc.ndvi AS ndvi_value,
                lc.relative_humidity AS relative_humidity_value,
                lc.surface_pressure_hpa AS surface_pressure_hpa_value,
                lc.nighttime_lights AS nighttime_lights_value
            FROM observation o
            JOIN beetle_species bs ON bs.beetle_id = o.beetle_id
            JOIN location l ON l.location_id = o.location_id
            LEFT JOIN media_agg ma ON ma.gbif_id = o.gbif_id
            {latest_snapshot_join_sql("l", "o")}
            {base_where_sql}
            UNION ALL
            SELECT
                'manual' AS source_type,
                br.record_id,
                {manual_entity_id_sql("br")} AS entity_id,
                br.gbif_id,
                br.event_date,
                br.basis_of_record,
                br.dataset_name,
                br.institution_code,
                br.image_available,
                br.taxon_id,
                br.scientific_name,
                br.family,
                br.genus,
                br.specific_epithet,
                br.latitude,
                br.longitude,
                br.city,
                br.region,
                br.country,
                br.verbatim_locality,
                br.coordinate_uncertainty,
                br.elevation,
                br.landcover_class,
                br.biome_id,
                br.ecoregion_id,
                br.distance_to_water_m,
                br.human_modification,
                br.slope,
                br.soil_ph,
                br.soil_organic_carbon,
                br.worldclim_bio01,
                br.worldclim_bio12,
                CASE
                    WHEN br.image_url IS NOT NULL AND TRIM(br.image_url) <> '' THEN 1
                    ELSE 0
                END AS media_count,
                br.media_license AS license_sample,
                br.image_url AS image_url_sample,
                br.temperature AS temperature_value,
                br.precipitation AS precipitation_value,
                br.soil_moisture AS soil_moisture_value,
                br.ndvi AS ndvi_value,
                br.relative_humidity AS relative_humidity_value,
                br.surface_pressure_hpa AS surface_pressure_hpa_value,
                br.nighttime_lights AS nighttime_lights_value
            FROM beetle_record br
            WHERE br.status = 'active'
        ),
        enriched AS (
            SELECT
                b.source_type,
                b.record_id,
                b.entity_id,
                b.gbif_id,
                b.event_date AS observedAt,
                b.scientific_name AS name,
                b.family,
                b.latitude AS lat,
                b.longitude AS lng,
                {location_fallback_sql("b")} AS location,
                {CLIMATE_CASE_SQL} AS climate,
                {VEGETATION_CASE_SQL} AS vegetation,
                {ELEVATION_GROUP_CASE_SQL} AS elevationGroup,
                {TEMPERATURE_BAND_CASE_SQL} AS temperature_band,
                {PRECIPITATION_BAND_CASE_SQL} AS precipitation_band,
                {SOIL_MOISTURE_BAND_CASE_SQL} AS soil_moisture_band,
                {NDVI_BAND_CASE_SQL} AS ndvi_band,
                {HUMIDITY_BAND_CASE_SQL} AS humidity_band,
                {PRESSURE_BAND_CASE_SQL} AS pressure_band,
                {LIGHT_POLLUTION_BAND_CASE_SQL} AS light_pollution_band,
                {SLOPE_BAND_CASE_SQL} AS slope_band,
                {WATER_DISTANCE_BAND_CASE_SQL} AS water_distance_band,
                {HUMAN_MODIFICATION_BAND_CASE_SQL} AS human_modification_band,
                {LANDCOVER_GROUP_CASE_SQL} AS landcover_group,
                {COORDINATE_UNCERTAINTY_BAND_CASE_SQL} AS coordinate_uncertainty_band,
                {SOIL_PH_BAND_CASE_SQL} AS soil_ph_band,
                {SOIL_CARBON_BAND_CASE_SQL} AS soil_carbon_band,
                {WORLCLIM_TEMP_BAND_CASE_SQL} AS worldclim_temp_band,
                {WORLDCLIM_PRECIP_BAND_CASE_SQL} AS worldclim_precip_band,
                {EVENT_DATE_QUALITY_CASE_SQL} AS event_date_quality,
                {BASIS_OF_RECORD_CASE_SQL} AS basis_of_record_class,
                {TAXON_RESOLUTION_CASE_SQL} AS taxon_resolution,
                {MEDIA_COVERAGE_CASE_SQL} AS media_coverage,
                {LICENSE_CLASS_CASE_SQL} AS license_class,
                b.coordinate_uncertainty,
                b.worldclim_bio01,
                b.worldclim_bio12,
                b.soil_ph,
                b.soil_organic_carbon,
                b.basis_of_record,
                b.dataset_name,
                b.institution_code,
                b.image_available,
                b.taxon_id,
                b.genus,
                b.specific_epithet,
                b.media_count,
                b.license_sample,
                b.image_url_sample,
                b.country,
                b.region,
                b.city,
                b.elevation,
                b.temperature_value AS temperature,
                b.precipitation_value AS precipitation,
                b.soil_moisture_value AS soil_moisture,
                b.ndvi_value AS ndvi,
                b.relative_humidity_value AS relative_humidity,
                b.surface_pressure_hpa_value AS surface_pressure_hpa,
                b.nighttime_lights_value AS nighttime_lights,
                b.slope,
                b.distance_to_water_m,
                b.human_modification,
                b.landcover_class,
                b.ecoregion_id,
                b.biome_id,
                {SOIL_CASE_SQL} AS soil
            FROM base b
        )
    """


def lean_enriched_cte_sql(base_where_sql: str) -> str:
    """Build lean list base+enriched CTE SQL with lightweight fields."""
    return f"""
        WITH base AS (
            SELECT
                'observation' AS source_type,
                NULL AS record_id,
                {observation_entity_id_sql("o")} AS entity_id,
                o.gbif_id,
                o.event_date,
                o.basis_of_record,
                o.dataset_name,
                o.institution_code,
                o.image_available,
                o.taxon_id,
                bs.scientific_name,
                bs.family,
                bs.genus,
                bs.specific_epithet,
                l.latitude,
                l.longitude,
                l.city,
                l.region,
                l.country,
                l.verbatim_locality,
                l.coordinate_uncertainty,
                l.elevation,
                l.landcover_class,
                l.biome_id,
                l.ecoregion_id,
                {normalized_soil_ph_sql("l")} AS soil_ph,
                {normalized_soil_organic_carbon_sql("l")} AS soil_organic_carbon,
                {normalized_worldclim_bio01_sql("l")} AS worldclim_bio01,
                l.worldclim_bio12,
                COALESCE(
                    lc.avg_temperature,
                    {normalized_worldclim_bio01_sql("l")}
                ) AS temperature_value,
                COALESCE(lc.precipitation, l.worldclim_bio12) AS precipitation_value
            FROM observation o
            JOIN beetle_species bs ON bs.beetle_id = o.beetle_id
            JOIN location l ON l.location_id = o.location_id
            {latest_snapshot_join_sql("l", "o")}
            {base_where_sql}
            UNION ALL
            SELECT
                'manual' AS source_type,
                br.record_id,
                {manual_entity_id_sql("br")} AS entity_id,
                br.gbif_id,
                br.event_date,
                br.basis_of_record,
                br.dataset_name,
                br.institution_code,
                br.image_available,
                br.taxon_id,
                br.scientific_name,
                br.family,
                br.genus,
                br.specific_epithet,
                br.latitude,
                br.longitude,
                br.city,
                br.region,
                br.country,
                br.verbatim_locality,
                br.coordinate_uncertainty,
                br.elevation,
                br.landcover_class,
                br.biome_id,
                br.ecoregion_id,
                br.soil_ph,
                br.soil_organic_carbon,
                br.worldclim_bio01,
                br.worldclim_bio12,
                br.temperature AS temperature_value,
                br.precipitation AS precipitation_value
            FROM beetle_record br
            WHERE br.status = 'active'
        ),
        enriched AS (
            SELECT
                b.source_type,
                b.record_id,
                b.entity_id,
                b.gbif_id,
                b.event_date AS observedAt,
                b.scientific_name AS name,
                b.family,
                b.latitude AS lat,
                b.longitude AS lng,
                {location_fallback_sql("b")} AS location,
                {CLIMATE_CASE_SQL} AS climate,
                {VEGETATION_CASE_SQL} AS vegetation,
                {ELEVATION_GROUP_CASE_SQL} AS elevationGroup,
                b.elevation,
                b.worldclim_bio01 AS temperature,
                {SOIL_CASE_SQL} AS soil,
                b.genus,
                b.specific_epithet,
                b.taxon_id,
                b.basis_of_record,
                b.dataset_name,
                b.institution_code,
                b.image_available,
                b.coordinate_uncertainty,
                b.country,
                b.region,
                b.city,
                b.soil_ph,
                b.soil_organic_carbon,
                b.worldclim_bio01,
                b.worldclim_bio12,
                b.landcover_class,
                b.ecoregion_id,
                b.biome_id
            FROM base b
        )
    """


def full_result_projection_sql(alias: str = "e") -> str:
    """Return the full result projection SQL for enriched beetle rows."""
    return f"""
            {alias}.source_type,
            {alias}.record_id,
            {alias}.entity_id,
            {alias}.gbif_id,
            {alias}.observedAt,
            {alias}.name,
            {alias}.family,
            {alias}.lat,
            {alias}.lng,
            {alias}.location,
            {alias}.climate,
            {alias}.vegetation,
            {alias}.elevationGroup,
            {alias}.elevation,
            {alias}.temperature,
            {alias}.soil,
            {alias}.temperature_band,
            {alias}.precipitation_band,
            {alias}.soil_moisture_band,
            {alias}.ndvi_band,
            {alias}.humidity_band,
            {alias}.pressure_band,
            {alias}.light_pollution_band,
            {alias}.slope_band,
            {alias}.water_distance_band,
            {alias}.human_modification_band,
            {alias}.landcover_group,
            {alias}.coordinate_uncertainty_band,
            {alias}.soil_ph_band,
            {alias}.soil_carbon_band,
            {alias}.worldclim_temp_band,
            {alias}.worldclim_precip_band,
            {alias}.event_date_quality,
            {alias}.basis_of_record_class,
            {alias}.taxon_resolution,
            {alias}.media_coverage,
            {alias}.license_class,
            {alias}.precipitation,
            {alias}.soil_moisture,
            {alias}.ndvi,
            {alias}.relative_humidity,
            {alias}.surface_pressure_hpa,
            {alias}.nighttime_lights,
            {alias}.slope,
            {alias}.distance_to_water_m,
            {alias}.human_modification,
            {alias}.landcover_class,
            {alias}.ecoregion_id,
            {alias}.biome_id,
            {alias}.coordinate_uncertainty,
            {alias}.worldclim_bio01,
            {alias}.worldclim_bio12,
            {alias}.soil_ph,
            {alias}.soil_organic_carbon,
            {alias}.basis_of_record,
            {alias}.dataset_name,
            {alias}.institution_code,
            {alias}.image_available,
            {alias}.taxon_id,
            {alias}.genus,
            {alias}.specific_epithet,
            {alias}.media_count,
            {alias}.license_sample,
            {alias}.image_url_sample,
            {alias}.country,
            {alias}.region,
            {alias}.city
    """


def compact_result_projection_sql(alias: str = "e") -> str:
    """Return the compact result projection SQL for beetle list read rows."""
    return f"""
            {alias}.entity_id,
            {alias}.gbif_id,
            {alias}.observed_at AS observedAt,
            {alias}.name,
            {alias}.family,
            {alias}.lat,
            {alias}.lng,
            {alias}.location,
            {alias}.climate,
            {alias}.vegetation,
            {alias}.elevation,
            NULL AS temperature,
            NULL AS soil,
            (
                SELECT MIN(m.image_url)
                FROM media m
                WHERE m.gbif_id = {alias}.gbif_id
                    AND m.image_url IS NOT NULL
                    AND TRIM(m.image_url) <> ''
            ) AS image_url_sample,
            {alias}.country,
            {alias}.elevation_group AS elevationGroup
    """


def compact_rows_select_sql(where_sql: str, order_by_sql: str) -> str:
    """Return compact read-model SELECT with filters, ordering, and pagination placeholders."""
    return f"""
        SELECT
            {compact_result_projection_sql("e")}
        FROM beetle_list_read e
        {where_sql}
        ORDER BY {order_by_sql}
        LIMIT :limit OFFSET :offset
    """


def _country_base_with_snapshot_cte_sql(base_columns_sql: str) -> str:
    """Return reusable country base CTE with snapshot-derived climate values."""
    return f"""
        WITH base AS (
            SELECT
                {base_columns_sql},
                {normalized_worldclim_bio01_sql("l")} AS worldclim_bio01,
                COALESCE(
                    lc.avg_temperature,
                    {normalized_worldclim_bio01_sql("l")}
                ) AS temperature_value,
                COALESCE(lc.precipitation, l.worldclim_bio12) AS precipitation_value
            FROM observation o
            JOIN location l ON l.location_id = o.location_id
            {latest_snapshot_join_sql("l", "o")}
            WHERE UPPER(COALESCE(l.country, '')) = :country_code
        )
    """


def country_overview_sql() -> str:
    """Return SQL for country-level overview metrics."""
    return f"""
        {_country_base_with_snapshot_cte_sql("o.beetle_id, l.country, l.elevation, l.landcover_class, l.biome_id")},
        enriched AS (
            SELECT
                b.beetle_id,
                b.country,
                b.elevation,
                b.temperature_value,
                b.precipitation_value,
                {CLIMATE_CASE_SQL} AS climate,
                {VEGETATION_CASE_SQL} AS vegetation
            FROM base b
        )
        SELECT
            COUNT(DISTINCT beetle_id) AS species_count,
            COUNT(*) AS observation_count,
            MIN(elevation) AS min_elevation,
            AVG(elevation) AS avg_elevation,
            MAX(elevation) AS max_elevation,
            AVG(temperature_value) AS avg_temperature,
            AVG(precipitation_value) AS avg_precipitation,
            MIN(country) AS country_name
        FROM enriched
    """


def country_top_climates_sql() -> str:
    """Return SQL for top climate buckets per country."""
    return f"""
        {_country_base_with_snapshot_cte_sql("l.country")},
        enriched AS (
            SELECT {CLIMATE_CASE_SQL} AS climate FROM base b
        )
        SELECT climate, COUNT(*) AS cnt
        FROM enriched
        GROUP BY climate
        ORDER BY cnt DESC, climate ASC
        LIMIT 3
    """


def country_top_vegetation_sql() -> str:
    """Return SQL for top vegetation buckets per country."""
    return f"""
        WITH base AS (
            SELECT l.country, l.landcover_class, l.biome_id
            FROM observation o
            JOIN location l ON l.location_id = o.location_id
            WHERE UPPER(COALESCE(l.country, '')) = :country_code
        ),
        enriched AS (
            SELECT {VEGETATION_CASE_SQL} AS vegetation FROM base b
        )
        SELECT vegetation, COUNT(*) AS cnt
        FROM enriched
        GROUP BY vegetation
        ORDER BY cnt DESC, vegetation ASC
        LIMIT 3
    """


def country_top_beetles_sql() -> str:
    """Return SQL for top beetle species per country."""
    return """
        SELECT
            bs.scientific_name AS name,
            bs.family AS family,
            COUNT(*) AS cnt
        FROM observation o
        JOIN location l ON l.location_id = o.location_id
        JOIN beetle_species bs ON bs.beetle_id = o.beetle_id
        WHERE UPPER(COALESCE(l.country, '')) = :country_code
        GROUP BY o.beetle_id, bs.scientific_name, bs.family
        ORDER BY cnt DESC, name ASC
        LIMIT 3
    """
