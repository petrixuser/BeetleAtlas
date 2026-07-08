"""SQL-Bausteine fuer die Kaefer-Listen- und Detailabfragen (Read-Pfad)."""
from backend.config.sql.classifications_sql import (
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
    """Liefert den SQL-Ausdruck, der Sentinel-/skalierte soil_ph-Werte normalisiert."""
    return f"""
                CASE
                    WHEN {location_alias}.soil_ph IS NULL OR {location_alias}.soil_ph = -9999 THEN NULL
                    WHEN {location_alias}.soil_ph > 14 THEN {location_alias}.soil_ph / 10
                    ELSE {location_alias}.soil_ph
                END
    """


def normalized_soil_organic_carbon_sql(location_alias: str = "l") -> str:
    """Liefert den SQL-Ausdruck, der soil_organic_carbon-Werte normalisiert."""
    return f"""
                CASE
                    WHEN {location_alias}.soil_organic_carbon IS NULL OR {location_alias}.soil_organic_carbon = -9999 THEN NULL
                    WHEN {location_alias}.soil_organic_carbon > 60 THEN {location_alias}.soil_organic_carbon / 5
                    ELSE {location_alias}.soil_organic_carbon
                END
    """


def normalized_worldclim_bio01_sql(location_alias: str = "l") -> str:
    """Liefert den SQL-Ausdruck, der BIO01-Temperaturwerte normalisiert."""
    return f"""
                CASE
                    WHEN {location_alias}.worldclim_bio01 IS NULL OR {location_alias}.worldclim_bio01 = -9999 THEN NULL
                    WHEN {location_alias}.worldclim_bio01 > 80 THEN {location_alias}.worldclim_bio01 / 10
                    ELSE {location_alias}.worldclim_bio01
                END
    """


def event_date_cutoff_sql(observation_alias: str = "o") -> str:
    """Liefert den SQL-Ausdruck fuer das Fallback-Stichdatum, das Snapshots nutzen."""
    return f"""
COALESCE(
                                                    {observation_alias}.event_date_parsed,
                          STR_TO_DATE(LEFT({observation_alias}.event_date, 10), '%Y-%m-%d'),
                          DATE('9999-12-31')
                      )
    """


def latest_snapshot_join_sql(location_alias: str = "l", observation_alias: str = "o") -> str:
    """Baut das LEFT-JOIN-SQL, das den letzten climate_snapshot zum Beobachtungszeitpunkt anhaengt."""
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
    """Liefert den SQL-Ausdruck fuer normalisierte entity_id von Beobachtungen."""
    return f"CONCAT('occ-', {observation_alias}.gbif_id)"


def manual_entity_id_sql(record_alias: str = "br") -> str:
    """Liefert den SQL-Ausdruck fuer normalisierte entity_id manueller Eintraege."""
    return f"CONCAT('rec-', {record_alias}.record_id)"


def location_fallback_sql(row_alias: str = "b", include_location_column: bool = False) -> str:
    """Liefert den SQL-Ausdruck fuer den normalisierten Anzeigetext des Orts (location)."""
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


def climate_major_sql(koppen_expr: str, fallback_sql: str) -> str:
    """Klima-Hauptgruppe (A-E): bevorzugt den vorberechneten Koeppen-Code
    faellt nur bei fehlendem Code auf die alte Temperatur-/Niederschlags-Heuristik
    zurueck. So sind Karte, Liste, Detail und Laenderpanel konsistent."""
    return f"""
        CASE
            WHEN {koppen_expr} IS NOT NULL AND {koppen_expr} <> '' THEN LEFT({koppen_expr}, 1)
            ELSE ({fallback_sql})
        END
    """


def full_enriched_cte_sql(base_where_sql: str, media_where_sql: str = "") -> str:
    """Baut das vollstaendige base+enriched-CTE-SQL fuer Liste/Detail inkl. Klassifizierungen."""
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
                l.koppen_code,
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
                NULL AS koppen_code,
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
                {climate_major_sql("b.koppen_code", CLIMATE_CASE_SQL)} AS climate,
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
    """Baut das schlanke base+enriched-CTE-SQL fuer die Liste mit leichtgewichtigen Feldern."""
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
                l.koppen_code,
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
                NULL AS koppen_code,
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
                {climate_major_sql("b.koppen_code", CLIMATE_CASE_SQL)} AS climate,
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
    """Liefert die vollstaendige Ergebnis-Projektion (SQL) fuer enriched-Kaeferzeilen."""
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
    """Liefert die kompakte Ergebnis-Projektion (SQL) fuer beetle_list_read-Zeilen."""
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
            {alias}.temperature,
            {alias}.precipitation,
            {alias}.soil_ph AS soilPh,
            {alias}.soil_ph_band AS soilPhBand,
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
    """Liefert das kompakte read-model-SELECT mit Filtern, Sortierung und Pagination-Platzhaltern."""
    return f"""
        SELECT
            {compact_result_projection_sql("e")}
        FROM beetle_list_read e
        {where_sql}
        ORDER BY {order_by_sql}
        LIMIT :limit OFFSET :offset
    """


def _country_base_with_snapshot_cte_sql(base_columns_sql: str) -> str:
    """Liefert das wiederverwendbare Land-base-CTE mit aus Snapshots abgeleiteten Klimawerten."""
    return f"""
        WITH base AS (
            SELECT
                {base_columns_sql},
                {normalized_worldclim_bio01_sql("l")} AS worldclim_bio01,
                COALESCE(
                    lc.avg_temperature,
                    {normalized_worldclim_bio01_sql("l")}
                ) AS temperature_value,
                NULLIF(l.worldclim_bio12, -9999) AS precipitation_value,
                NULLIF(lc.soil_moisture, -9999) AS soil_moisture_value,
                NULLIF(lc.ndvi, -9999) AS ndvi_value,
                NULLIF(NULLIF(lc.relative_humidity, -9999), 0) AS humidity_value,
                NULLIF(NULLIF(lc.surface_pressure_hpa, -9999), 0) AS pressure_value,
                NULLIF(lc.nighttime_lights, -9999) AS light_value,
                NULLIF(l.slope, -9999) AS slope_value,
                NULLIF(l.distance_to_water_m, -9999) AS water_distance_value,
                NULLIF(l.human_modification, -9999) AS human_modification_value,
                CASE
                    WHEN l.soil_ph IS NULL OR l.soil_ph = -9999 OR l.soil_ph <= 0 THEN NULL
                    WHEN l.soil_ph > 14 THEN l.soil_ph / 10
                    ELSE l.soil_ph
                END AS soil_ph_value
            FROM observation o
            JOIN location l ON l.location_id = o.location_id
            {latest_snapshot_join_sql("l", "o")}
            WHERE l.country = :country_code
        )
    """


def country_overview_sql() -> str:
    """Liefert das SQL fuer die Uebersichts-Kennzahlen auf Landesebene."""
    return f"""
        {_country_base_with_snapshot_cte_sql("o.beetle_id, l.country, l.elevation, l.landcover_class, l.biome_id")},
        enriched AS (
            SELECT
                b.beetle_id,
                b.country,
                b.elevation,
                b.temperature_value,
                b.precipitation_value,
                b.soil_moisture_value,
                b.ndvi_value,
                b.humidity_value,
                b.soil_ph_value,
                b.pressure_value,
                b.light_value,
                b.slope_value,
                b.water_distance_value,
                b.human_modification_value,
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
            MIN(temperature_value) AS min_temperature,
            AVG(temperature_value) AS avg_temperature,
            MAX(temperature_value) AS max_temperature,
            MIN(precipitation_value) AS min_precipitation,
            AVG(precipitation_value) AS avg_precipitation,
            MAX(precipitation_value) AS max_precipitation,
            MIN(soil_moisture_value) AS min_soil_moisture,
            AVG(soil_moisture_value) AS avg_soil_moisture,
            MAX(soil_moisture_value) AS max_soil_moisture,
            MIN(ndvi_value) AS min_ndvi,
            AVG(ndvi_value) AS avg_ndvi,
            MAX(ndvi_value) AS max_ndvi,
            MIN(humidity_value) AS min_humidity,
            AVG(humidity_value) AS avg_humidity,
            MAX(humidity_value) AS max_humidity,
            MIN(soil_ph_value) AS min_soil_ph,
            AVG(soil_ph_value) AS avg_soil_ph,
            MAX(soil_ph_value) AS max_soil_ph,
            MIN(pressure_value) AS min_pressure,
            AVG(pressure_value) AS avg_pressure,
            MAX(pressure_value) AS max_pressure,
            MIN(light_value) AS min_light,
            AVG(light_value) AS avg_light,
            MAX(light_value) AS max_light,
            MIN(slope_value) AS min_slope,
            AVG(slope_value) AS avg_slope,
            MAX(slope_value) AS max_slope,
            MIN(water_distance_value) AS min_water_distance,
            AVG(water_distance_value) AS avg_water_distance,
            MAX(water_distance_value) AS max_water_distance,
            MIN(human_modification_value) AS min_human_modification,
            AVG(human_modification_value) AS avg_human_modification,
            MAX(human_modification_value) AS max_human_modification,
            MIN(country) AS country_name
        FROM enriched
    """


def country_top_climates_sql() -> str:
    """Top Klima-Hauptgruppen (A-E) je Land, abgeleitet aus dem vorberechneten
    Koeppen-Subtyp (koppen_code). So sind Hauptgruppen und Subtypen (country_top_koppen_sql)
    konsistent und entsprechen den Kartenpolygonen (Standard Koeppen-Geiger)."""
    return """
        SELECT LEFT(l.koppen_code, 1) AS climate, COUNT(*) AS cnt
        FROM observation o
        JOIN location l ON l.location_id = o.location_id
        WHERE l.country = :country_code AND l.koppen_code IS NOT NULL AND l.koppen_code <> ''
        GROUP BY LEFT(l.koppen_code, 1)
        ORDER BY cnt DESC, climate ASC
        LIMIT 5
    """


def country_top_vegetation_sql() -> str:
    """Liefert das SQL fuer die haeufigsten Vegetations-Buckets je Land."""
    return f"""
        WITH base AS (
            SELECT l.country, l.landcover_class, l.biome_id
            FROM observation o
            JOIN location l ON l.location_id = o.location_id
            WHERE l.country = :country_code
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


def country_top_koppen_sql() -> str:
    """Top Koeppen-Subtypen (vorberechnete Kartenzonen) je Land."""
    return """
        SELECT l.koppen_code AS koppen, COUNT(*) AS cnt
        FROM observation o
        JOIN location l ON l.location_id = o.location_id
        WHERE l.country = :country_code AND l.koppen_code IS NOT NULL AND l.koppen_code <> ''
        GROUP BY l.koppen_code
        ORDER BY cnt DESC, koppen ASC
        LIMIT 6
    """


def country_top_vegetation_zone_sql() -> str:
    """Top Vegetationszonen (vorberechnete Oekoregionen) je Land."""
    return """
        SELECT l.vegetation_zone AS zone, COUNT(*) AS cnt
        FROM observation o
        JOIN location l ON l.location_id = o.location_id
        WHERE l.country = :country_code AND l.vegetation_zone IS NOT NULL AND l.vegetation_zone <> ''
        GROUP BY l.vegetation_zone
        ORDER BY cnt DESC, zone ASC
        LIMIT 6
    """


def country_top_beetles_sql() -> str:
    """Liefert das SQL fuer die haeufigsten Kaeferarten je Land."""
    return """
        SELECT
            bs.scientific_name AS name,
            bs.family AS family,
            COUNT(*) AS cnt
        FROM observation o
        JOIN location l ON l.location_id = o.location_id
        JOIN beetle_species bs ON bs.beetle_id = o.beetle_id
        WHERE l.country = :country_code
        GROUP BY o.beetle_id, bs.scientific_name, bs.family
        ORDER BY cnt DESC, name ASC
        LIMIT 3
    """
