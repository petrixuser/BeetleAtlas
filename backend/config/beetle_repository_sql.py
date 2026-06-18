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


def full_enriched_cte_sql(base_where_sql: str) -> str:
    """Build full list/detail base+enriched CTE SQL with classifications."""
    return f"""
        WITH media_agg AS (
            SELECT
                m.gbif_id,
                COUNT(*) AS media_count,
                MIN(m.license) AS license_sample,
                MIN(m.image_url) AS image_url_sample
            FROM media m
            GROUP BY m.gbif_id
        ),
        base AS (
            SELECT
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
        ),
        enriched AS (
            SELECT
                b.gbif_id,
                b.event_date AS observedAt,
                b.scientific_name AS name,
                b.family,
                b.latitude AS lat,
                b.longitude AS lng,
                COALESCE(
                    NULLIF(b.verbatim_locality, ''),
                    NULLIF(CONCAT_WS(', ', b.city, b.region, b.country), ''),
                    NULLIF(CONCAT_WS(', ', b.region, b.country), ''),
                    b.country,
                    'Unbekannt'
                ) AS location,
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
                l.worldclim_bio12
            FROM observation o
            JOIN beetle_species bs ON bs.beetle_id = o.beetle_id
            JOIN location l ON l.location_id = o.location_id
            {base_where_sql}
        ),
        enriched AS (
            SELECT
                b.gbif_id,
                b.event_date AS observedAt,
                b.scientific_name AS name,
                b.family,
                b.latitude AS lat,
                b.longitude AS lng,
                COALESCE(
                    NULLIF(b.verbatim_locality, ''),
                    NULLIF(CONCAT_WS(', ', b.city, b.region, b.country), ''),
                    NULLIF(CONCAT_WS(', ', b.region, b.country), ''),
                    b.country,
                    'Unbekannt'
                ) AS location,
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
