
VEGETATION_CASE_SQL = """
CASE
    WHEN b.landcover_class = 10 THEN 'tree_cover'
    WHEN b.landcover_class = 20 THEN 'shrubland'
    WHEN b.landcover_class = 30 THEN 'grassland'
    WHEN b.landcover_class = 40 THEN 'cropland'
    WHEN b.landcover_class = 50 THEN 'built_up'
    WHEN b.landcover_class = 60 THEN 'bare_sparse'
    WHEN b.landcover_class = 70 THEN 'snow_ice'
    WHEN b.landcover_class = 80 THEN 'water'
    WHEN b.landcover_class = 90 THEN 'wetland'
    WHEN b.landcover_class = 95 THEN 'mangroves'
    WHEN b.landcover_class = 100 THEN 'moss_lichen'
    ELSE 'unknown'
END
"""


LANDCOVER_GROUP_CASE_SQL = """
CASE
    WHEN b.landcover_class = 10 THEN 'tree_cover'
    WHEN b.landcover_class = 20 THEN 'shrubland'
    WHEN b.landcover_class = 30 THEN 'grassland'
    WHEN b.landcover_class = 40 THEN 'cropland'
    WHEN b.landcover_class = 50 THEN 'built_up'
    WHEN b.landcover_class = 60 THEN 'bare_sparse'
    WHEN b.landcover_class = 70 THEN 'snow_ice'
    WHEN b.landcover_class = 80 THEN 'water'
    WHEN b.landcover_class = 90 THEN 'wetland'
    WHEN b.landcover_class = 95 THEN 'mangroves'
    WHEN b.landcover_class = 100 THEN 'moss_lichen'
    ELSE 'unknown'
END
"""


SOIL_CASE_SQL = """
CASE
    WHEN (b.soil_ph IS NULL OR b.soil_ph = -9999) AND (b.soil_organic_carbon IS NULL OR b.soil_organic_carbon = -9999) THEN 'unknown'
    WHEN b.soil_ph IS NOT NULL AND b.soil_ph <> -9999 AND b.soil_ph < 5.5 THEN 'strongly_acidic'
    WHEN b.soil_ph IS NOT NULL AND b.soil_ph <> -9999 AND b.soil_ph < 6.5 THEN 'acidic'
    WHEN b.soil_ph IS NOT NULL AND b.soil_ph <> -9999 AND b.soil_ph <= 7.5 THEN 'neutral'
    WHEN b.soil_ph IS NOT NULL AND b.soil_ph <> -9999 AND b.soil_ph <= 8.5 THEN 'alkaline'
    WHEN b.soil_ph IS NOT NULL AND b.soil_ph <> -9999 THEN 'strongly_alkaline'
    WHEN b.soil_organic_carbon < 2 THEN 'very_low_carbon'
    WHEN b.soil_organic_carbon < 5 THEN 'low_carbon'
    WHEN b.soil_organic_carbon < 10 THEN 'moderate_carbon'
    WHEN b.soil_organic_carbon < 20 THEN 'high_carbon'
    ELSE 'very_high_carbon'
END
"""


ELEVATION_GROUP_CASE_SQL = """
CASE
    WHEN b.elevation IS NULL THEN 'low'
    WHEN b.elevation < 500 THEN 'low'
    WHEN b.elevation < 1500 THEN 'mid'
    WHEN b.elevation < 3000 THEN 'high'
    ELSE 'veryHigh'
END
"""



SOIL_MOISTURE_BAND_CASE_SQL = """
CASE
    WHEN b.soil_moisture_value IS NULL OR b.soil_moisture_value = -9999 THEN 'unknown'
    WHEN b.soil_moisture_value < 0.10 THEN 'very_dry'
    WHEN b.soil_moisture_value < 0.20 THEN 'dry'
    WHEN b.soil_moisture_value < 0.35 THEN 'moist'
    ELSE 'wet'
END
"""


NDVI_BAND_CASE_SQL = """
CASE
    WHEN b.ndvi_value IS NULL OR b.ndvi_value = -9999 THEN 'unknown'
    WHEN b.ndvi_value < 0.10 THEN 'barren'
    WHEN b.ndvi_value < 0.30 THEN 'sparse_vegetation'
    WHEN b.ndvi_value < 0.50 THEN 'moderate_vegetation'
    ELSE 'dense_vegetation'
END
"""


HUMIDITY_BAND_CASE_SQL = """
CASE
    WHEN b.relative_humidity_value IS NULL OR b.relative_humidity_value = -9999 THEN 'unknown'
    WHEN b.relative_humidity_value < 30 THEN 'dry_air'
    WHEN b.relative_humidity_value < 60 THEN 'moderate_humidity'
    WHEN b.relative_humidity_value < 80 THEN 'humid_air'
    ELSE 'very_humid_air'
END
"""


PRESSURE_BAND_CASE_SQL = """
CASE
    WHEN b.surface_pressure_hpa_value IS NULL OR b.surface_pressure_hpa_value = -9999 THEN 'unknown'
    WHEN b.surface_pressure_hpa_value < 700 THEN 'extreme_low_pressure'
    WHEN b.surface_pressure_hpa_value < 850 THEN 'very_low_pressure'
    WHEN b.surface_pressure_hpa_value < 950 THEN 'low_pressure'
    WHEN b.surface_pressure_hpa_value <= 1050 THEN 'normal_pressure'
    ELSE 'high_pressure'
END
"""


LIGHT_POLLUTION_BAND_CASE_SQL = """
CASE
    WHEN b.nighttime_lights_value IS NULL OR b.nighttime_lights_value = -9999 THEN 'unknown'
    WHEN b.nighttime_lights_value < 1 THEN 'dark'
    WHEN b.nighttime_lights_value < 5 THEN 'low_light'
    WHEN b.nighttime_lights_value < 20 THEN 'moderate_light'
    ELSE 'bright_light'
END
"""


SLOPE_BAND_CASE_SQL = """
CASE
    WHEN b.slope IS NULL OR b.slope = -9999 THEN 'unknown'
    WHEN b.slope < 2 THEN 'level'
    WHEN b.slope < 5 THEN 'gentle'
    WHEN b.slope < 15 THEN 'moderate'
    WHEN b.slope < 30 THEN 'steep'
    ELSE 'very_steep'
END
"""


WATER_DISTANCE_BAND_CASE_SQL = """
CASE
    WHEN b.distance_to_water_m IS NULL OR b.distance_to_water_m = -9999 THEN 'unknown'
    WHEN b.distance_to_water_m < 100 THEN 'riparian'
    WHEN b.distance_to_water_m < 500 THEN 'near_water'
    WHEN b.distance_to_water_m < 2000 THEN 'intermediate_distance'
    WHEN b.distance_to_water_m < 10000 THEN 'inland'
    ELSE 'far_inland'
END
"""


HUMAN_MODIFICATION_BAND_CASE_SQL = """
CASE
    WHEN b.human_modification IS NULL OR b.human_modification = -9999 THEN 'unknown'
    WHEN b.human_modification < 0.10 THEN 'natural'
    WHEN b.human_modification < 0.30 THEN 'low_modification'
    WHEN b.human_modification < 0.60 THEN 'moderate_modification'
    ELSE 'high_modification'
END
"""


COORDINATE_UNCERTAINTY_BAND_CASE_SQL = """
CASE
    WHEN b.coordinate_uncertainty IS NULL OR TRIM(b.coordinate_uncertainty) = '' THEN 'unknown'
    WHEN b.coordinate_uncertainty REGEXP '^[0-9]+(\\.[0-9]+)?$' = 0 THEN 'nicht_numerisch'
    WHEN CAST(b.coordinate_uncertainty AS DECIMAL(12,2)) < 100 THEN 'hochpraezise'
    WHEN CAST(b.coordinate_uncertainty AS DECIMAL(12,2)) < 1000 THEN 'moderat'
    WHEN CAST(b.coordinate_uncertainty AS DECIMAL(12,2)) < 5000 THEN 'unscharf'
    ELSE 'sehr_unscharf'
END
"""


SOIL_PH_BAND_CASE_SQL = """
CASE
    WHEN b.soil_ph IS NULL OR b.soil_ph = -9999 OR b.soil_ph < 0 THEN 'unknown'
    WHEN b.soil_ph < 5.5 THEN 'strongly_acidic'
    WHEN b.soil_ph < 6.5 THEN 'acidic'
    WHEN b.soil_ph <= 7.5 THEN 'neutral'
    WHEN b.soil_ph <= 8.5 THEN 'alkaline'
    ELSE 'strongly_alkaline'
END
"""


SOIL_CARBON_BAND_CASE_SQL = """
CASE
    WHEN b.soil_organic_carbon IS NULL OR b.soil_organic_carbon = -9999 OR b.soil_organic_carbon < 0 THEN 'unknown'
    WHEN b.soil_organic_carbon < 2 THEN 'very_low_carbon'
    WHEN b.soil_organic_carbon < 5 THEN 'low_carbon'
    WHEN b.soil_organic_carbon < 10 THEN 'moderate_carbon'
    WHEN b.soil_organic_carbon < 20 THEN 'high_carbon'
    ELSE 'very_high_carbon'
END
"""


WORLCLIM_TEMP_BAND_CASE_SQL = """
CASE
    WHEN b.worldclim_bio01 IS NULL OR b.worldclim_bio01 = -9999 THEN 'unknown'
    WHEN b.worldclim_bio01 < 10 THEN 'cold'
    WHEN b.worldclim_bio01 < 18 THEN 'mild'
    WHEN b.worldclim_bio01 < 24 THEN 'warm'
    ELSE 'hot'
END
"""


WORLDCLIM_PRECIP_BAND_CASE_SQL = """
CASE
    WHEN b.worldclim_bio12 IS NULL OR b.worldclim_bio12 = -9999 THEN 'unknown'
    WHEN b.worldclim_bio12 < 250 THEN 'arid'
    WHEN b.worldclim_bio12 < 500 THEN 'semi_arid'
    WHEN b.worldclim_bio12 < 1000 THEN 'sub_humid'
    WHEN b.worldclim_bio12 < 2000 THEN 'humid'
    ELSE 'per_humid'
END
"""

TEMPERATURE_BAND_CASE_SQL = """
CASE
    WHEN b.temperature_value IS NULL OR b.temperature_value = -9999 THEN 'unknown'
    WHEN b.temperature_value < 10 THEN 'cold'
    WHEN b.temperature_value < 18 THEN 'mild'
    WHEN b.temperature_value < 24 THEN 'warm'
    ELSE 'hot'
END
"""

CLIMATE_CASE_SQL = WORLCLIM_TEMP_BAND_CASE_SQL

PRECIPITATION_BAND_CASE_SQL = """
CASE
    WHEN b.precipitation_value IS NULL OR b.precipitation_value = -9999 THEN 'unknown'
    WHEN b.precipitation_value < 250 THEN 'arid'
    WHEN b.precipitation_value < 500 THEN 'semi_arid'
    WHEN b.precipitation_value < 1000 THEN 'sub_humid'
    WHEN b.precipitation_value < 2000 THEN 'humid'
    ELSE 'per_humid'
END
"""

EVENT_DATE_QUALITY_CASE_SQL = """
CASE
    WHEN b.event_date IS NULL OR TRIM(b.event_date) = '' THEN 'unknown'
    WHEN b.event_date REGEXP '^[0-9]{4}-[0-9]{2}-[0-9]{2}$' THEN 'vollstaendig'
    WHEN b.event_date REGEXP '^[0-9]{4}-[0-9]{2}$' THEN 'jahr_monat'
    WHEN b.event_date REGEXP '^[0-9]{4}$' THEN 'nur_jahr'
    ELSE 'frei_text'
END
"""


BASIS_OF_RECORD_CASE_SQL = """
CASE
    WHEN b.basis_of_record IS NULL OR TRIM(b.basis_of_record) = '' THEN 'unknown'
    WHEN UPPER(b.basis_of_record) LIKE '%HUMAN_OBSERVATION%' THEN 'beobachtung'
    WHEN UPPER(b.basis_of_record) LIKE '%MACHINE_OBSERVATION%' THEN 'sensor'
    WHEN UPPER(b.basis_of_record) LIKE '%PRESERVED_SPECIMEN%' THEN 'beleg'
    WHEN UPPER(b.basis_of_record) LIKE '%MATERIAL_SAMPLE%' THEN 'probe'
    ELSE 'sonstiges'
END
"""


LICENSE_CLASS_CASE_SQL = """
CASE
    WHEN b.license_sample IS NULL OR TRIM(b.license_sample) = '' THEN 'unknown'
    WHEN LOWER(b.license_sample) LIKE '%cc0%' OR LOWER(b.license_sample) LIKE '%cc-by%' THEN 'offen'
    ELSE 'unklar_oder_restriktiv'
END
"""


TAXON_RESOLUTION_CASE_SQL = """
CASE
    WHEN b.scientific_name IS NOT NULL AND TRIM(b.scientific_name) <> ''
         AND b.genus IS NOT NULL AND TRIM(b.genus) <> ''
         AND b.specific_epithet IS NOT NULL AND TRIM(b.specific_epithet) <> '' THEN 'artniveau'
    WHEN b.genus IS NOT NULL AND TRIM(b.genus) <> '' THEN 'gattungsniveau'
    WHEN b.family IS NOT NULL AND TRIM(b.family) <> '' THEN 'familienniveau'
    ELSE 'unaufgeloest'
END
"""


MEDIA_COVERAGE_CASE_SQL = """
CASE
    WHEN b.media_count IS NULL OR b.media_count = 0 THEN 'keine_bilder'
    WHEN b.media_count = 1 THEN 'ein_bild'
    WHEN b.media_count <= 5 THEN 'mehrere_bilder'
    ELSE 'viele_bilder'
END
"""
