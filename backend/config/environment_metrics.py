"""Kanonischer Katalog der Umwelt-Metriken fuer die Quicklook-Wertebereiche.

Einzige Quelle fuer die Liste dieser Metriken:
  * die Repository-Abfrage (fetch_environment_ranges) baut daraus die MIN/MAX-
    SQL-Spalten (min_<spalte>/max_<spalte>),
  * der Controller (_build_environment_ranges_payload) baut daraus das API-Payload.
So bleiben SQL-Spalten und Payload-Schluessel garantiert synchron.

Jeder Eintrag: (db_spalte, payload_schluessel)
"""

ENVIRONMENT_METRICS = [
    ("elevation", "elevation"),
    ("temperature", "temperature"),
    ("worldclim_bio01", "worldclimBio01"),
    ("precipitation", "precipitation"),
    ("worldclim_bio12", "worldclimBio12"),
    ("soil_moisture", "soilMoisture"),
    ("ndvi", "ndvi"),
    ("relative_humidity", "relativeHumidity"),
    ("surface_pressure_hpa", "surfacePressureHpa"),
    ("nighttime_lights", "nighttimeLights"),
    ("slope", "slope"),
    ("distance_to_water_m", "distanceToWaterM"),
    ("human_modification", "humanModification"),
]
