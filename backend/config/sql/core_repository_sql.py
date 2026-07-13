"""SQL fuer Kernstatistiken (Zeilenzahlen der Haupttabellen)."""
STATS_OVERVIEW_SQL = """
SELECT 'beetle_species' AS table_name, COUNT(*) AS rows_count FROM beetle_species
UNION ALL SELECT 'location', COUNT(*) FROM location
UNION ALL SELECT 'observation', COUNT(*) FROM observation
UNION ALL SELECT 'media', COUNT(*) FROM media
UNION ALL SELECT 'climate_snapshot', COUNT(*) FROM climate_snapshot
"""

SPECIES_COUNT_SQL = "SELECT COUNT(*) AS total FROM beetle_species"

OBSERVATIONS_COUNT_SQL_TEMPLATE = """
SELECT COUNT(*) AS total
FROM observation o
JOIN beetle_species bs ON bs.beetle_id = o.beetle_id
{where_sql}
"""

CLIMATE_BY_LOCATION_SQL_TEMPLATE = """
SELECT
    location_id,
    snapshot_date,
    avg_temperature,
    precipitation,
    soil_moisture,
    ndvi,
    relative_humidity,
    surface_pressure_hpa,
    nighttime_lights
FROM climate_snapshot
{where_sql}
ORDER BY snapshot_date
LIMIT :limit
"""

QUALITY_TOTALS_SQL = """
SELECT
    (SELECT COUNT(*) FROM observation) AS observation_count,
    (SELECT COUNT(*) FROM location) AS location_count,
    (SELECT COUNT(*) FROM climate_snapshot) AS climate_snapshot_count
"""

QUALITY_OBSERVATION_NULLS_SQL = """
SELECT
    SUM(CASE WHEN o.event_date IS NULL OR TRIM(o.event_date) = '' THEN 1 ELSE 0 END) AS event_date_missing,
    SUM(CASE WHEN o.event_date_parsed IS NULL THEN 1 ELSE 0 END) AS event_date_parsed_missing,
    SUM(CASE WHEN o.basis_of_record IS NULL OR TRIM(o.basis_of_record) = '' THEN 1 ELSE 0 END) AS basis_of_record_missing,
    SUM(CASE WHEN o.taxon_id IS NULL THEN 1 ELSE 0 END) AS taxon_id_missing,
    SUM(CASE WHEN o.location_id IS NULL THEN 1 ELSE 0 END) AS location_id_missing,
    SUM(CASE WHEN o.image_available IS NULL THEN 1 ELSE 0 END) AS image_available_missing
FROM observation o
"""

QUALITY_LOCATION_NULLS_SQL = """
SELECT
    SUM(CASE WHEN l.latitude IS NULL THEN 1 ELSE 0 END) AS latitude_missing,
    SUM(CASE WHEN l.longitude IS NULL THEN 1 ELSE 0 END) AS longitude_missing,
    SUM(CASE WHEN l.elevation IS NULL THEN 1 ELSE 0 END) AS elevation_missing,
    SUM(CASE WHEN l.coordinate_uncertainty IS NULL THEN 1 ELSE 0 END) AS coordinate_uncertainty_missing,
    SUM(CASE WHEN l.worldclim_bio01 IS NULL OR l.worldclim_bio01 = -9999 THEN 1 ELSE 0 END) AS worldclim_bio01_missing,
    SUM(CASE WHEN l.worldclim_bio12 IS NULL OR l.worldclim_bio12 = -9999 THEN 1 ELSE 0 END) AS worldclim_bio12_missing,
    SUM(CASE WHEN l.soil_ph IS NULL OR l.soil_ph = -9999 THEN 1 ELSE 0 END) AS soil_ph_missing,
    SUM(CASE WHEN l.soil_organic_carbon IS NULL OR l.soil_organic_carbon = -9999 THEN 1 ELSE 0 END) AS soil_organic_carbon_missing
FROM location l
"""

QUALITY_SNAPSHOT_NULLS_SQL = """
SELECT
    SUM(CASE WHEN cs.avg_temperature IS NULL THEN 1 ELSE 0 END) AS avg_temperature_missing,
    SUM(CASE WHEN cs.precipitation IS NULL THEN 1 ELSE 0 END) AS precipitation_missing,
    SUM(CASE WHEN cs.soil_moisture IS NULL THEN 1 ELSE 0 END) AS soil_moisture_missing,
    SUM(CASE WHEN cs.ndvi IS NULL THEN 1 ELSE 0 END) AS ndvi_missing,
    SUM(CASE WHEN cs.relative_humidity IS NULL THEN 1 ELSE 0 END) AS relative_humidity_missing,
    SUM(CASE WHEN cs.surface_pressure_hpa IS NULL THEN 1 ELSE 0 END) AS surface_pressure_hpa_missing,
    SUM(CASE WHEN cs.nighttime_lights IS NULL THEN 1 ELSE 0 END) AS nighttime_lights_missing
FROM climate_snapshot cs
"""

QUALITY_EE_COVERAGE_SQL = """
SELECT
    COUNT(*) AS total_observations,
    SUM(
        CASE WHEN EXISTS (
            SELECT 1
            FROM climate_snapshot cs
            WHERE cs.location_id = o.location_id
              AND cs.snapshot_date <= COALESCE(
                                            o.event_date_parsed,
                  STR_TO_DATE(LEFT(o.event_date, 10), '%Y-%m-%d'),
                  DATE('9999-12-31')
              )
        ) THEN 1 ELSE 0 END
    ) AS with_snapshot_match
FROM observation o
"""

INSERT_QUALITY_REPORT_HISTORY_SQL = """
INSERT INTO quality_report_history (
    generated_at,
    source_label,
    observation_count,
    location_count,
    climate_snapshot_count,
    observation_null_rates_json,
    location_null_rates_json,
    climate_snapshot_null_rates_json,
    ee_coverage_json
)
VALUES (
    UTC_TIMESTAMP(),
    :source_label,
    :observation_count,
    :location_count,
    :climate_snapshot_count,
    CAST(:observation_null_rates_json AS JSON),
    CAST(:location_null_rates_json AS JSON),
    CAST(:climate_snapshot_null_rates_json AS JSON),
    CAST(:ee_coverage_json AS JSON)
)
"""

QUALITY_REPORT_HISTORY_LIST_SQL = """
SELECT
    quality_report_id,
    generated_at,
    source_label,
    observation_count,
    location_count,
    climate_snapshot_count,
    observation_null_rates_json,
    location_null_rates_json,
    climate_snapshot_null_rates_json,
    ee_coverage_json
FROM quality_report_history
ORDER BY quality_report_id DESC
LIMIT :limit OFFSET :offset
"""

QUALITY_REPORT_HISTORY_COUNT_SQL = "SELECT COUNT(*) AS total FROM quality_report_history"

QUALITY_REPORT_HISTORY_BY_ID_SQL = """
SELECT
    quality_report_id,
    generated_at,
    source_label,
    observation_count,
    location_count,
    climate_snapshot_count,
    observation_null_rates_json,
    location_null_rates_json,
    climate_snapshot_null_rates_json,
    ee_coverage_json
FROM quality_report_history
WHERE quality_report_id = :quality_report_id
LIMIT 1
"""


def build_species_sql(order_by_sql: str) -> str:
    """Baut das paginierte SQL fuer die Artenliste mit dynamischem ORDER BY."""
    return f"""
    SELECT
        beetle_id,
        taxon_id,
        family,
        genus,
        specific_epithet,
        scientific_name
    FROM beetle_species
    ORDER BY {order_by_sql}
    LIMIT :limit OFFSET :offset
    """


def build_observations_sql(where_sql: str, order_by_sql: str) -> str:
    """Baut das paginierte SQL fuer Beobachtungen mit dynamischem WHERE und ORDER BY."""
    return f"""
    SELECT
        o.gbif_id,
        o.beetle_id,
        o.location_id,
        o.event_date,
        o.dataset_name,
        o.image_available,
        bs.scientific_name
    FROM observation o
    JOIN beetle_species bs ON bs.beetle_id = o.beetle_id
    {where_sql}
    ORDER BY {order_by_sql}
    LIMIT :limit OFFSET :offset
    """
