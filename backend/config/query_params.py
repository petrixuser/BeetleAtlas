"""Wiederverwendbare FastAPI-Query-Parameter fuer Listen-/Filter-Endpunkte."""
from typing import Dict, Optional

from fastapi import Query


ELEVATION_PATTERN = "^(0_100|100_500|500_1000|1000_2000|2000_3000|3000_4500|4500_plus|ultra_low_0_100|low_100_500|lower_mid_500_1000|upper_mid_1000_2000|high_2000_3000|very_high_3000_4500|extreme_high_4500_plus|e0_100|e100_500|e500_1000|e1000_2000|e2000_3000|e3000_4500|e4500_plus)(,(0_100|100_500|500_1000|1000_2000|2000_3000|3000_4500|4500_plus|ultra_low_0_100|low_100_500|lower_mid_500_1000|upper_mid_1000_2000|high_2000_3000|very_high_3000_4500|extreme_high_4500_plus|e0_100|e100_500|e500_1000|e1000_2000|e2000_3000|e3000_4500|e4500_plus))*$"

LIST_LIMIT_DEFAULT = 100
LIST_LIMIT_MAX = 50000
LIST_OFFSET_MIN = 0

MAP_LIMIT_DEFAULT = 500
MAP_LIMIT_MAX = 5000
MAP_OFFSET_MIN = 0
MAP_ZOOM_DEFAULT = 6
MAP_ZOOM_MIN = 0
MAP_ZOOM_MAX = 24

OBSERVED_YEAR_MIN = 2000
OBSERVED_YEAR_MAX = 2026

BEETLE_SORT_BY_PATTERN = "^(id|name|family|observedAt|elevation|temperature|climate|vegetation)$"
MAP_SORT_BY_PATTERN = "^(speciesName|observedAt|elevation|climate|vegetation)$"
SORT_DIR_PATTERN = "^(asc|desc)$"


def beetle_query_params(
	q: Optional[str] = Query(None, max_length=200),
	country: Optional[str] = Query(None, max_length=255),
	climate: Optional[str] = Query(None),
	vegetation: Optional[str] = Query(None),
	elevation: Optional[str] = Query(
		None,
		pattern=ELEVATION_PATTERN,
	),
	temperature_band: Optional[str] = Query(None),
	precipitation_band: Optional[str] = Query(None),
	soil_moisture_band: Optional[str] = Query(None),
	ndvi_band: Optional[str] = Query(None),
	humidity_band: Optional[str] = Query(None),
	pressure_band: Optional[str] = Query(None),
	light_pollution_band: Optional[str] = Query(None),
	slope_band: Optional[str] = Query(None),
	water_distance_band: Optional[str] = Query(None),
	human_impact_band: Optional[str] = Query(None),
	landcover_group: Optional[str] = Query(None),
	coordinate_uncertainty_band: Optional[str] = Query(None),
	soil_ph_band: Optional[str] = Query(None),
	soil_carbon_band: Optional[str] = Query(None),
	worldclim_temp_band: Optional[str] = Query(None),
	worldclim_precip_band: Optional[str] = Query(None),
	event_date_quality: Optional[str] = Query(None),
	observed_year: Optional[int] = Query(None, ge=OBSERVED_YEAR_MIN, le=OBSERVED_YEAR_MAX),
	basis_of_record_class: Optional[str] = Query(None),
	taxon_resolution: Optional[str] = Query(None),
	media_coverage: Optional[str] = Query(None),
	has_image: Optional[bool] = Query(None),
	license_class: Optional[str] = Query(None),
	bbox: Optional[str] = Query(None),
	limit: int = Query(LIST_LIMIT_DEFAULT, ge=1, le=LIST_LIMIT_MAX),
	offset: int = Query(LIST_OFFSET_MIN, ge=LIST_OFFSET_MIN),
	compact: bool = Query(False),
	sort_by: str = Query(
		"id",
		pattern=BEETLE_SORT_BY_PATTERN,
	),
	sort_dir: str = Query("asc", pattern=SORT_DIR_PATTERN),
) -> Dict[str, object]:
	"""Definiert und liefert validierte Query-Parameter fuer die Kaefer-Listenfilterung."""
	return {
		"q": q,
		"country": country,
		"climate": climate,
		"vegetation": vegetation,
		"elevation": elevation,
		"temperature_band": temperature_band,
		"precipitation_band": precipitation_band,
		"soil_moisture_band": soil_moisture_band,
		"ndvi_band": ndvi_band,
		"humidity_band": humidity_band,
		"pressure_band": pressure_band,
		"light_pollution_band": light_pollution_band,
		"slope_band": slope_band,
		"water_distance_band": water_distance_band,
		"human_impact_band": human_impact_band,
		"landcover_group": landcover_group,
		"coordinate_uncertainty_band": coordinate_uncertainty_band,
		"soil_ph_band": soil_ph_band,
		"soil_carbon_band": soil_carbon_band,
		"worldclim_temp_band": worldclim_temp_band,
		"worldclim_precip_band": worldclim_precip_band,
		"event_date_quality": event_date_quality,
		"observed_year": observed_year,
		"basis_of_record_class": basis_of_record_class,
		"taxon_resolution": taxon_resolution,
		"media_coverage": media_coverage,
		"has_image": has_image,
		"license_class": license_class,
		"bbox": bbox,
		"limit": limit,
		"offset": offset,
		"compact": compact,
		"sort_by": sort_by,
		"sort_dir": sort_dir,
	}


def map_query_params(
	bbox: str = Query(...),
	zoom: int = Query(MAP_ZOOM_DEFAULT, ge=MAP_ZOOM_MIN, le=MAP_ZOOM_MAX),
	q: Optional[str] = Query(None, max_length=200),
	country: Optional[str] = Query(None, max_length=255),
	climate: Optional[str] = Query(None),
	vegetation: Optional[str] = Query(None),
	elevation: Optional[str] = Query(
		None,
		pattern=ELEVATION_PATTERN,
	),
	temperature_band: Optional[str] = Query(None),
	precipitation_band: Optional[str] = Query(None),
	soil_moisture_band: Optional[str] = Query(None),
	ndvi_band: Optional[str] = Query(None),
	humidity_band: Optional[str] = Query(None),
	pressure_band: Optional[str] = Query(None),
	light_pollution_band: Optional[str] = Query(None),
	slope_band: Optional[str] = Query(None),
	water_distance_band: Optional[str] = Query(None),
	human_impact_band: Optional[str] = Query(None),
	landcover_group: Optional[str] = Query(None),
	coordinate_uncertainty_band: Optional[str] = Query(None),
	soil_ph_band: Optional[str] = Query(None),
	soil_carbon_band: Optional[str] = Query(None),
	worldclim_temp_band: Optional[str] = Query(None),
	worldclim_precip_band: Optional[str] = Query(None),
	event_date_quality: Optional[str] = Query(None),
	observed_year: Optional[int] = Query(None, ge=OBSERVED_YEAR_MIN, le=OBSERVED_YEAR_MAX),
	basis_of_record_class: Optional[str] = Query(None),
	taxon_resolution: Optional[str] = Query(None),
	media_coverage: Optional[str] = Query(None),
	has_image: Optional[bool] = Query(None),
	license_class: Optional[str] = Query(None),
	limit: int = Query(MAP_LIMIT_DEFAULT, ge=1, le=MAP_LIMIT_MAX),
	offset: int = Query(MAP_OFFSET_MIN, ge=MAP_OFFSET_MIN),
	sort_by: str = Query(
		"speciesName",
		pattern=MAP_SORT_BY_PATTERN,
	),
	sort_dir: str = Query("asc", pattern=SORT_DIR_PATTERN),
) -> Dict[str, object]:
	"""Definiert und liefert validierte Query-Parameter fuer Kartenpunkt-Anfragen."""
	return {
		"bbox": bbox,
		"zoom": zoom,
		"q": q,
		"country": country,
		"climate": climate,
		"vegetation": vegetation,
		"elevation": elevation,
		"temperature_band": temperature_band,
		"precipitation_band": precipitation_band,
		"soil_moisture_band": soil_moisture_band,
		"ndvi_band": ndvi_band,
		"humidity_band": humidity_band,
		"pressure_band": pressure_band,
		"light_pollution_band": light_pollution_band,
		"slope_band": slope_band,
		"water_distance_band": water_distance_band,
		"human_impact_band": human_impact_band,
		"landcover_group": landcover_group,
		"coordinate_uncertainty_band": coordinate_uncertainty_band,
		"soil_ph_band": soil_ph_band,
		"soil_carbon_band": soil_carbon_band,
		"worldclim_temp_band": worldclim_temp_band,
		"worldclim_precip_band": worldclim_precip_band,
		"event_date_quality": event_date_quality,
		"observed_year": observed_year,
		"basis_of_record_class": basis_of_record_class,
		"taxon_resolution": taxon_resolution,
		"media_coverage": media_coverage,
		"has_image": has_image,
		"license_class": license_class,
		"limit": limit,
		"offset": offset,
		"sort_by": sort_by,
		"sort_dir": sort_dir,
	}
