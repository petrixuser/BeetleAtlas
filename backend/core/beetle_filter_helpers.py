"""Hilfsfunktionen zum Aufbau von SQL-WHERE-Klauseln fuer Kaefer-Filter
(Klima-Haupt-/Subtypen, Vegetationsschluessel/-zonen und exakte Filter)."""

from typing import Any, Dict, List, Optional

from backend.config.beetle_filters import FILTER_COLUMN_MAP
from backend.config.climate_subtypes import is_climate_subtype_code, parent_climate_code


# Grobe Vegetations-Schluessel (Landbedeckungs-/Biom-Gruppen) der Read-Model-Spalte
COARSE_VEGETATION_KEYS = frozenset(
    {
        "tree_cover",
        "shrubland",
        "grassland",
        "cropland",
        "built_up",
        "bare_sparse",
        "snow_ice",
        "water",
        "wetland",
        "mangroves",
        "moss_lichen",
        "unknown",
    }
)


def _split_csv(raw_value: Optional[str]) -> List[str]:
    """Zerlegt eine optionale CSV-Stringangabe in eine Liste von nicht-leeren Strings."""
    return [part.strip() for part in str(raw_value or "").split(",") if part.strip()]


def raw_climate_has_subtype(raw_climate: Optional[str]) -> bool:
    """Prueft, ob in der Roh-Klimaangabe mindestens ein Subtyp-Code enthalten ist."""
    return any(is_climate_subtype_code(v) for v in _split_csv(raw_climate))


def raw_vegetation_has_zone(raw_vegetation: Optional[str]) -> bool:
    """Prueft, ob die Roh-Vegetationsangabe eine feine Zone (kein grober Schluessel) enthaelt."""
    return any(v not in COARSE_VEGETATION_KEYS for v in _split_csv(raw_vegetation))


def _in_clause(params: Dict[str, Any], column: str, key_prefix: str, values: List[str]) -> Optional[str]:
    """Baut eine ``col = :x`` bzw. ``col IN (...)`` Klausel und registriert Params."""
    if not values:
        return None
    if len(values) == 1:
        params[f"{key_prefix}_0"] = values[0]
        return f"{column} = :{key_prefix}_0"
    placeholders: List[str] = []
    for idx, value in enumerate(values):
        param_key = f"{key_prefix}_{idx}"
        placeholders.append(f":{param_key}")
        params[param_key] = value
    return f"{column} IN ({', '.join(placeholders)})"


def append_climate_filter(
    filters: List[str],
    params: Dict[str, Any],
    major_column: str,
    raw_climate: Optional[str],
    koppen_column: Optional[str] = None,
) -> None:
    """Filtert nach Koeppen-Hauptgruppen (A-E) und – falls verfuegbar – nach den
    vorberechneten Subtyp-Codes (``koppen_column``). Subtypen wie ``Af`` nutzen die
    precomputed Spalte, damit die Auswahl exakt den Kartenpolygonen entspricht.
    """
    values = _split_csv(raw_climate)
    if not values:
        return
    majors = [v for v in values if not is_climate_subtype_code(v)]
    subtypes = [v for v in values if is_climate_subtype_code(v)]

    clauses: List[str] = []
    major_clause = _in_clause(params, major_column, "climate", majors)
    if major_clause:
        clauses.append(major_clause)

    if subtypes and koppen_column:
        sub_clause = _in_clause(params, koppen_column, "koppen", subtypes)
        if sub_clause:
            clauses.append(sub_clause)
    elif subtypes:
        # Kein precomputed Subtyp-Spalte (Live-Pfad): auf Hauptgruppe zurueckfallen.
        mapped: List[str] = []
        for value in subtypes:
            major = parent_climate_code(value)
            if major and major not in mapped:
                mapped.append(major)
        fallback = _in_clause(params, major_column, "climate_sub", mapped)
        if fallback:
            clauses.append(fallback)

    if clauses:
        filters.append("(" + " OR ".join(clauses) + ")")


def append_vegetation_filter(
    filters: List[str],
    params: Dict[str, Any],
    coarse_column: str,
    raw_vegetation: Optional[str],
    zone_column: Optional[str] = None,
) -> None:
    """Filtert grobe Vegetationsschluessel ueber ``coarse_column`` und praezise
    Kartenzonen (deutsche Oekoregion-Namen) ueber die vorberechnete ``zone_column``.
    """
    values = _split_csv(raw_vegetation)
    if not values:
        return
    coarse = [v for v in values if v in COARSE_VEGETATION_KEYS]
    zones = [v for v in values if v not in COARSE_VEGETATION_KEYS]

    clauses: List[str] = []
    coarse_clause = _in_clause(params, coarse_column, "veg", coarse)
    if coarse_clause:
        clauses.append(coarse_clause)

    if zones and zone_column:
        zone_clause = _in_clause(params, zone_column, "vegzone", zones)
        if zone_clause:
            clauses.append(zone_clause)

    if clauses:
        filters.append("(" + " OR ".join(clauses) + ")")


def apply_exact_filters(filters: List[str], params: Dict[str, Any], requested_filters: Dict[str, Optional[str]]) -> None:
    """Wendet exakte SQL-Match-Filter aus den angefragten Filterwerten an."""
    for key, column in FILTER_COLUMN_MAP.items():
        value = requested_filters.get(key)
        if not value:
            continue

        if isinstance(value, str):
            values = [part.strip() for part in value.split(",") if part.strip()]
            if len(values) > 1:
                placeholders = []
                for idx, item in enumerate(values):
                    param_key = f"{key}_{idx}"
                    placeholders.append(f":{param_key}")
                    params[param_key] = item
                filters.append(f"{column} IN ({', '.join(placeholders)})")
                continue
            if len(values) == 1:
                value = values[0]

        filters.append(f"{column} = :{key}")
        params[key] = value
