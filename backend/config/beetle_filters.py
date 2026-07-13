"""Zuordnung von Filter-Schluesseln auf SQL-Spalten fuer Listen-/Kartenfilter."""
FILTER_COLUMN_MAP = {
    "country": "e.country",
    "climate": "e.climate",
    "vegetation": "e.vegetation",
    "elevation": "e.elevationGroup",
    "temperature_band": "e.temperature_band",
    "precipitation_band": "e.precipitation_band",
    "soil_moisture_band": "e.soil_moisture_band",
    "ndvi_band": "e.ndvi_band",
    "humidity_band": "e.humidity_band",
    "pressure_band": "e.pressure_band",
    "light_pollution_band": "e.light_pollution_band",
    "slope_band": "e.slope_band",
    "water_distance_band": "e.water_distance_band",
    "human_impact_band": "e.human_modification_band",
    "landcover_group": "e.landcover_group",
    "coordinate_uncertainty_band": "e.coordinate_uncertainty_band",
    "soil_ph_band": "e.soil_ph_band",
    "soil_carbon_band": "e.soil_carbon_band",
    "worldclim_temp_band": "e.worldclim_temp_band",
    "worldclim_precip_band": "e.worldclim_precip_band",
    "event_date_quality": "e.event_date_quality",
    "basis_of_record_class": "e.basis_of_record_class",
    "taxon_resolution": "e.taxon_resolution",
    "media_coverage": "e.media_coverage",
    "license_class": "e.license_class",
}

ADVANCED_FILTER_KEYS = (
    "temperature_band",
    "precipitation_band",
    "soil_moisture_band",
    "ndvi_band",
    "humidity_band",
    "pressure_band",
    "light_pollution_band",
    "slope_band",
    "water_distance_band",
    "human_impact_band",
    "landcover_group",
    "coordinate_uncertainty_band",
    "soil_ph_band",
    "soil_carbon_band",
    "worldclim_temp_band",
    "worldclim_precip_band",
    "event_date_quality",
    "basis_of_record_class",
    "taxon_resolution",
    "media_coverage",
    "license_class",
)

COMPACT_FAST_ADVANCED_FILTER_KEYS = frozenset(
    {
        "soil_ph_band",
        "temperature_band",
        "precipitation_band",
        "event_date_quality",
    }
)

COMPACT_PRECOMPUTED_DIM_FILTER_MAP = {
    "country": "country",
    "climate": "climate",
    "vegetation": "vegetation",
    "elevation": "elevation_group",
    "soil_ph_band": "soil_ph_band",
    "temperature_band": "temperature_band",
    "precipitation_band": "precipitation_band",
    "event_date_quality": "event_date_quality",
}
