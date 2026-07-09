"""Controller-Funktionen fuer Kaefer-Listen, Detailansicht, Medien,
Laender-Aggregationen und Umwelt-Wertebereiche inklusive In-Memory-Caches."""

import time
from collections import OrderedDict
from threading import Lock
from typing import Any, Dict, List, Optional, cast

from backend.controllers.core_controller import (
    parse_bbox_or_error,
    raise_api_error,
    resolve_order_clause_or_error,
    validate_pagination_or_error,
)

from backend.config.beetle_filters import (
    ADVANCED_FILTER_KEYS,
    COMPACT_FAST_ADVANCED_FILTER_KEYS,
    COMPACT_PRECOMPUTED_DIM_FILTER_MAP,
)
from backend.config.climate_subtypes import is_climate_subtype_code, parent_climate_code
from backend.config.environment_metrics import ENVIRONMENT_METRICS
from backend.config.data.country_mappings import COUNTRY_CODE_TO_LOCATION_NAME
from backend.config.country_aliases import country_filter_candidates, ISO_TO_DISPLAY_NAME
from backend.config.error_codes import ERR
from backend.core.beetle_filter_helpers import (
    append_climate_filter,
    append_vegetation_filter,
    apply_exact_filters,
    raw_climate_has_subtype,
    raw_vegetation_has_zone,
)
from backend.core.payloads import to_beetle_payload, to_beetle_payload_compact
from backend.repositories.beetle_repository import (
    fetch_beetle_detail_row_by_entity,
    fetch_beetle_media_rows,
    fetch_beetle_media_rows_total,
    fetch_beetles_list_compact_rows,
    fetch_beetles_list_compact_total_precomputed,
    fetch_beetles_list_compact_total,
    fetch_beetles_list_lean,
    fetch_beetles_list_rows_total,
    fetch_country_detail_rows,
    fetch_country_list_count,
    fetch_environment_ranges,
    fetch_featured_beetle_rows,
    resolve_stored_country_value,
)
from backend.repositories.beetle_write_repository import (
    fetch_beetle_record_by_id,
    fetch_beetle_record_media_rows,
)


ENV_RANGES_CACHE: Optional[Dict[str, Any]] = None
ENV_RANGES_CACHE_TS: Optional[float] = None
ENV_RANGES_TTL_SECONDS = 60 * 30

_LIST_TOTAL_CACHE_TTL_SECONDS = 60
_LIST_TOTAL_CACHE_MAX_ITEMS = 512
_list_total_cache: "OrderedDict[tuple, tuple[float, int]]" = OrderedDict()
_list_total_cache_lock = Lock()

def _compact_total_cache_key(where_sql: str, params: Dict[str, Any]) -> tuple:
    """Baut einen stabilen Cache-Schluessel aus WHERE-SQL und Filter-Parametern."""
    filtered = []
    for key, value in params.items():
        if key in {"offset", "limit"}:
            continue
        filtered.append((key, value))
    filtered.sort(key=lambda item: item[0])
    return (where_sql, tuple(filtered))


def _compact_total_cache_get(key: tuple) -> Optional[int]:
    """Liest eine gecachte Gesamtzahl; entfernt abgelaufene Eintraege."""
    now = time.time()
    with _list_total_cache_lock:
        cached = _list_total_cache.get(key)
        if not cached:
            return None
        expires_at, total = cached
        if expires_at <= now:
            _list_total_cache.pop(key, None)
            return None
        _list_total_cache.move_to_end(key)
        return total


def _compact_total_cache_set(key: tuple, total: int) -> None:
    """Legt eine Gesamtzahl im LRU-Cache ab und begrenzt dessen Groesse."""
    with _list_total_cache_lock:
        _list_total_cache[key] = (time.time() + _LIST_TOTAL_CACHE_TTL_SECONDS, int(total))
        _list_total_cache.move_to_end(key)
        while len(_list_total_cache) > _LIST_TOTAL_CACHE_MAX_ITEMS:
            _list_total_cache.popitem(last=False)


def _compact_single_precomputed_dim(
    *,
    q: Optional[str],
    bbox: Optional[str],
    requested_filters: Dict[str, Optional[str]],
    observed_year: Optional[int],
    has_image: Optional[bool],
    raw_climate: Optional[str] = None,
    raw_vegetation: Optional[str] = None,
) -> Optional[tuple[str, str]]:
    """Ermittelt, ob genau EINE vorberechenbare Filter-Dimension aktiv ist."""
    # Vorberechnete Gesamtzahlen gelten nur fuer einfache Filter mit einer Dimension.
    if q or bbox:
        return None
    if raw_climate_has_subtype(raw_climate) or raw_vegetation_has_zone(raw_vegetation):
        return None

    active: list[tuple[str, str]] = []
    for filter_name, dim_name in COMPACT_PRECOMPUTED_DIM_FILTER_MAP.items():
        value = requested_filters.get(filter_name)
        if value:
            active.append((dim_name, str(value)))
    if observed_year is not None:
        active.append(("observed_year", str(observed_year)))
    if has_image is not None:
        active.append(("has_image", "1" if has_image else "0"))

    if len(active) != 1:
        return None
    # Land nutzt Name+ISO-Kandidaten (Alias) -> nicht vorberechenbar. Exakter
    # COUNT ueber die Kandidaten, damit die Listen-Trefferzahl mit der
    # Panel-"Funde"-Zahl (beetle_list_read) exakt uebereinstimmt.
    if requested_filters.get("country"):
        return None
    return active[0]


def _append_exact_or_in_filter(
    filters: List[str],
    params: Dict[str, Any],
    column: str,
    key: str,
    raw_value: Optional[str],
) -> None:
    """Haengt einen Gleichheits- (=) oder Mehrwert-Filter (IN) an die WHERE-Liste an."""
    if not raw_value:
        return

    values = [part.strip() for part in str(raw_value).split(",") if part.strip()]
    if not values:
        return
    if len(values) == 1:
        filters.append(f"{column} = :{key}")
        params[key] = values[0]
        return

    placeholders: List[str] = []
    for idx, value in enumerate(values):
        param_key = f"{key}_{idx}"
        placeholders.append(f":{param_key}")
        params[param_key] = value
    filters.append(f"{column} IN ({', '.join(placeholders)})")


def _normalize_climate_filter(raw_climate: Optional[str]) -> Optional[str]:
    """Fuehrt Klima-Subtyp-Codes auf ihren Hauptcode zurueck (dedupliziert)."""
    if not raw_climate:
        return raw_climate

    values = [part.strip() for part in str(raw_climate).split(",") if part.strip()]
    if not values:
        return None

    normalized: list[str] = []
    for value in values:
        if is_climate_subtype_code(value):
            major = parent_climate_code(value)
            if major and major not in normalized:
                normalized.append(major)
            continue
        if value not in normalized:
            normalized.append(value)

    if not normalized:
        return None
    return ",".join(normalized)


def _expand_event_date_quality_filter(raw_quality: Optional[str]) -> Optional[str]:
    """Erweitert Datumsqualitaets-Aliasse (deutsch/englisch) auf alle Synonyme."""
    if not raw_quality:
        return raw_quality

    alias_map: Dict[str, tuple[str, ...]] = {
        "vollstaendig": ("vollstaendig", "complete_date"),
        "complete_date": ("vollstaendig", "complete_date"),
        "jahr_monat": ("jahr_monat", "year_month_only"),
        "year_month_only": ("jahr_monat", "year_month_only"),
        "nur_jahr": ("nur_jahr", "year_only"),
        "year_only": ("nur_jahr", "year_only"),
        "frei_text": ("frei_text", "missing_or_invalid"),
        "missing_or_invalid": ("frei_text", "missing_or_invalid"),
        "unknown": ("unknown",),
    }

    values = [part.strip().lower() for part in str(raw_quality).split(",") if part.strip()]
    if not values:
        return None

    normalized: List[str] = []
    for value in values:
        aliases = alias_map.get(value, (value,))
        for alias in aliases:
            if alias not in normalized:
                normalized.append(alias)

    if not normalized:
        return None
    return ",".join(normalized)


def _build_environment_ranges_payload(row: Dict[str, Any]) -> Dict[str, Any]:
    """Baut aus einer Min-/Max-Zeile das Umweltbereichs-Payload (min/max je Metrik).

    Nutzt den zentralen ENVIRONMENT_METRICS-Katalog, damit Payload-Schluessel und
    SQL-Spalten synchron bleiben.
    """
    def _pair(column: str):
        """Liefert {min, max} als Floats fuer die Spalten min_<column>/max_<column>."""
        min_value = row.get(f"min_{column}")
        max_value = row.get(f"max_{column}")
        return {
            "min": float(min_value) if min_value is not None else None,
            "max": float(max_value) if max_value is not None else None,
        }

    return {payload_key: _pair(column) for column, payload_key in ENVIRONMENT_METRICS}


def warm_environment_ranges_cache(force: bool = False) -> Optional[Dict[str, Any]]:
    """Waermt oder aktualisiert den Umwelt-Wertebereich-Cache. Gibt das Cache-Payload zurueck, falls vorhanden."""
    global ENV_RANGES_CACHE, ENV_RANGES_CACHE_TS

    now = time.time()
    if (
        not force
        and ENV_RANGES_CACHE is not None
        and ENV_RANGES_CACHE_TS is not None
        and (now - ENV_RANGES_CACHE_TS) < ENV_RANGES_TTL_SECONDS
    ):
        return ENV_RANGES_CACHE

    row = fetch_environment_ranges()
    ENV_RANGES_CACHE = _build_environment_ranges_payload(row)
    ENV_RANGES_CACHE_TS = now
    return ENV_RANGES_CACHE


def _parse_entity_id_or_error(beetle_id: str) -> str:
    """Normalisiert die angefragte beetle id in die Form occ-* oder rec-*."""
    normalized = beetle_id.strip()
    if normalized.startswith("occ-"):
        numeric_part = normalized[4:]
        if not numeric_part.isdigit():
            raise_api_error(400, ERR.BEETLE.INVALID_ID, "Ungueltige ID. Erwartet z. B. occ-123, rec-456 oder 123.")
        return f"occ-{numeric_part}"
    if normalized.startswith("rec-"):
        numeric_part = normalized[4:]
        if not numeric_part.isdigit():
            raise_api_error(400, ERR.BEETLE.INVALID_ID, "Ungueltige ID. Erwartet z. B. occ-123, rec-456 oder 123.")
        return f"rec-{numeric_part}"
    if normalized.isdigit():
        return f"occ-{normalized}"

    raise_api_error(400, ERR.BEETLE.INVALID_ID, "Ungueltige ID. Erwartet z. B. occ-123, rec-456 oder 123.")
    raise AssertionError("unreachable")


def _build_list_order_by_sql(sort_by: str, sort_dir: str) -> str:
    """Bildet Sortier-Parameter auf eine sichere ORDER-BY-Klausel ab."""
    return resolve_order_clause_or_error(
        sort_by,
        sort_dir,
        {
            "id": "e.entity_id",
            "name": "e.name",
            "family": "e.family",
            "observedAt": "e.observedAt",
            "elevation": "e.elevation",
            "temperature": "e.temperature",
            "climate": "e.climate",
            "vegetation": "e.vegetation",
        },
    )


def _build_requested_filters(
    *,
    country: Optional[str],
    climate: Optional[str],
    vegetation: Optional[str],
    elevation: Optional[str],
    temperature_band: Optional[str],
    precipitation_band: Optional[str],
    soil_moisture_band: Optional[str],
    ndvi_band: Optional[str],
    humidity_band: Optional[str],
    pressure_band: Optional[str],
    light_pollution_band: Optional[str],
    slope_band: Optional[str],
    water_distance_band: Optional[str],
    human_impact_band: Optional[str],
    landcover_group: Optional[str],
    coordinate_uncertainty_band: Optional[str],
    soil_ph_band: Optional[str],
    soil_carbon_band: Optional[str],
    worldclim_temp_band: Optional[str],
    worldclim_precip_band: Optional[str],
    event_date_quality: Optional[str],
    basis_of_record_class: Optional[str],
    taxon_resolution: Optional[str],
    media_coverage: Optional[str],
    license_class: Optional[str],
) -> Dict[str, Optional[str]]:
    """Buendelt alle einzelnen Filter-Parameter in ein Dictionary."""
    return {
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
        "basis_of_record_class": basis_of_record_class,
        "taxon_resolution": taxon_resolution,
        "media_coverage": media_coverage,
        "license_class": license_class,
    }


def _build_list_where_sql_and_params(
    *,
    q: Optional[str],
    requested_filters: Dict[str, Optional[str]],
    elevation: Optional[str],
    expanded_event_date_quality: Optional[str],
    observed_year: Optional[int],
    has_image: Optional[bool],
    bbox: Optional[str],
    compact: bool,
    offset: int,
    raw_climate: Optional[str] = None,
    raw_vegetation: Optional[str] = None,
) -> tuple[str, Dict[str, Any]]:
    """Baut die WHERE-Klausel und die gebundenen Parameter fuer die Listenabfrage."""
    filters: List[str] = []
    params: Dict[str, Any] = {"offset": offset}

    if q:
        filters.append(
            """
            (
                e.name LIKE :q
                OR e.family LIKE :q
                OR e.location LIKE :q
            )
            """
        )
        params["q"] = f"%{q.strip()}%"

    requested_filters_for_exact = dict(requested_filters)
    requested_filters_for_exact["elevation"] = None
    requested_filters_for_exact["event_date_quality"] = None
    if requested_filters_for_exact.get("country"):
        requested_filters_for_exact["country"] = ",".join(
            country_filter_candidates(requested_filters_for_exact["country"])
        )
    if compact:
        requested_filters_for_exact["climate"] = None
        requested_filters_for_exact["vegetation"] = None
        append_climate_filter(filters, params, "e.climate", raw_climate, "e.koppen_code")
        append_vegetation_filter(filters, params, "e.vegetation", raw_vegetation, "e.vegetation_zone")
    apply_exact_filters(filters, params, requested_filters_for_exact)

    _append_exact_or_in_filter(
        filters,
        params,
        "e.elevation_group" if compact else "e.elevationGroup",
        "elevation",
        elevation,
    )
    _append_exact_or_in_filter(
        filters,
        params,
        "e.event_date_quality",
        "event_date_quality",
        expanded_event_date_quality,
    )

    if observed_year is not None:
        if compact:
            filters.append("e.observed_year = :observed_year")
            params["observed_year"] = int(observed_year)
        else:
            filters.append("SUBSTRING(e.observedAt, 1, 4) = :observed_year")
            params["observed_year"] = str(observed_year)

    if has_image is not None:
        if compact:
            filters.append("e.has_image = :has_image")
            params["has_image"] = 1 if has_image else 0
        elif has_image:
            filters.append("e.media_coverage <> 'keine_bilder'")
        else:
            filters.append("e.media_coverage = 'keine_bilder'")

    if bbox:
        bbox_params = parse_bbox_or_error(bbox)
        filters.append("(e.lng BETWEEN :min_lng AND :max_lng AND e.lat BETWEEN :min_lat AND :max_lat)")
        params.update(bbox_params)

    where_sql = ""
    if filters:
        where_sql = "WHERE " + " AND ".join(filters)

    return where_sql, params


def build_read_model_where(
    *,
    q: Optional[str] = None,
    country: Optional[str] = None,
    climate: Optional[str] = None,
    vegetation: Optional[str] = None,
    elevation: Optional[str] = None,
    soil_ph_band: Optional[str] = None,
    temperature_band: Optional[str] = None,
    precipitation_band: Optional[str] = None,
    event_date_quality: Optional[str] = None,
    observed_year: Optional[int] = None,
    has_image: Optional[bool] = None,
    bbox: Optional[str] = None,
) -> tuple[str, Dict[str, Any]]:
    """Baut eine kompakte WHERE-Klausel + Params (beetle_list_read, Alias ``e``).

    Nutzt die Listen-Filter-Pipeline wieder, damit Aufrufer (z. B. der Karten-
    Cluster-Pfad) identisch zu /api/beetles filtern. Es werden nur Filter
    akzeptiert, die auf beetle_list_read vorhanden sind; rein live-basierte
    erweiterte Baender sind hier absichtlich keine Parameter.
    """
    normalized_climate = _normalize_climate_filter(climate)
    expanded_event_date_quality = _expand_event_date_quality_filter(event_date_quality)
    requested_filters = _build_requested_filters(
        country=country,
        climate=normalized_climate,
        vegetation=vegetation,
        elevation=elevation,
        temperature_band=temperature_band,
        precipitation_band=precipitation_band,
        soil_moisture_band=None,
        ndvi_band=None,
        humidity_band=None,
        pressure_band=None,
        light_pollution_band=None,
        slope_band=None,
        water_distance_band=None,
        human_impact_band=None,
        landcover_group=None,
        coordinate_uncertainty_band=None,
        soil_ph_band=soil_ph_band,
        soil_carbon_band=None,
        worldclim_temp_band=None,
        worldclim_precip_band=None,
        event_date_quality=event_date_quality,
        basis_of_record_class=None,
        taxon_resolution=None,
        media_coverage=None,
        license_class=None,
    )
    return _build_list_where_sql_and_params(
        q=q,
        requested_filters=requested_filters,
        elevation=elevation,
        expanded_event_date_quality=expanded_event_date_quality,
        observed_year=observed_year,
        has_image=has_image,
        bbox=bbox,
        compact=True,
        offset=0,
        raw_climate=climate,
        raw_vegetation=vegetation,
    )


def _has_advanced_filters(requested_filters: Dict[str, Optional[str]]) -> bool:
    """True, wenn erweiterte Filter aktiv sind, die nicht kompakt schnell sind."""
    return any(
        requested_filters.get(key)
        for key in ADVANCED_FILTER_KEYS
        if key not in COMPACT_FAST_ADVANCED_FILTER_KEYS
    )


def _fetch_list_rows_total_and_payload_builder(
    *,
    compact: bool,
    has_advanced_filters: bool,
    where_sql: str,
    order_by_sql: str,
    limit: int,
    offset: int,
    params: Dict[str, Any],
    q: Optional[str],
    bbox: Optional[str],
    requested_filters: Dict[str, Optional[str]],
    observed_year: Optional[int],
    has_image: Optional[bool],
    raw_climate: Optional[str] = None,
    raw_vegetation: Optional[str] = None,
):
    """Waehlt den passenden Read-Pfad, laedt Zeilen + Gesamtzahl und den Payload-Builder."""
    payload_builder = to_beetle_payload

    if compact and not has_advanced_filters:
        rows = fetch_beetles_list_compact_rows(
            where_sql=where_sql,
            order_by_sql=order_by_sql,
            limit=limit,
            offset=offset,
            params=params,
        )
        total_cache_key = _compact_total_cache_key(where_sql, params)
        cached_total = _compact_total_cache_get(total_cache_key)
        if cached_total is None:
            precomputed_dim = _compact_single_precomputed_dim(
                q=q,
                bbox=bbox,
                requested_filters=requested_filters,
                observed_year=observed_year,
                has_image=has_image,
                raw_climate=raw_climate,
                raw_vegetation=raw_vegetation,
            )
            precomputed_total = None
            if precomputed_dim is not None:
                precomputed_total = fetch_beetles_list_compact_total_precomputed(
                    precomputed_dim[0],
                    precomputed_dim[1],
                )
            total = (
                precomputed_total
                if precomputed_total is not None
                else fetch_beetles_list_compact_total(where_sql=where_sql, params=params)
            )
            _compact_total_cache_set(total_cache_key, total)
        else:
            total = cached_total
        payload_builder = to_beetle_payload_compact
        return rows, total, payload_builder

    fetch = fetch_beetles_list_rows_total if has_advanced_filters else fetch_beetles_list_lean
    rows, total = fetch(
        where_sql=where_sql,
        base_where_sql="",
        order_by_sql=order_by_sql,
        limit=limit,
        offset=offset,
        params=params,
    )
    return rows, total, payload_builder

def list_beetles_controller(
    q: Optional[str],
    country: Optional[str],
    climate: Optional[str],
    vegetation: Optional[str],
    elevation: Optional[str],
    temperature_band: Optional[str],
    precipitation_band: Optional[str],
    soil_moisture_band: Optional[str],
    ndvi_band: Optional[str],
    humidity_band: Optional[str],
    pressure_band: Optional[str],
    light_pollution_band: Optional[str],
    slope_band: Optional[str],
    water_distance_band: Optional[str],
    human_impact_band: Optional[str],
    landcover_group: Optional[str],
    coordinate_uncertainty_band: Optional[str],
    soil_ph_band: Optional[str],
    soil_carbon_band: Optional[str],
    worldclim_temp_band: Optional[str],
    worldclim_precip_band: Optional[str],
    event_date_quality: Optional[str],
    observed_year: Optional[int],
    basis_of_record_class: Optional[str],
    taxon_resolution: Optional[str],
    media_coverage: Optional[str],
    has_image: Optional[bool],
    license_class: Optional[str],
    bbox: Optional[str],
    limit: int,
    offset: int,
    sort_by: str,
    sort_dir: str,
    compact: bool = False,
):
    """Gibt eine paginierte Kaefer-Liste anhand von Basis- und erweiterten Filtern sowie optionaler bbox zurueck.

    Nutzt einen schlanken Query-Pfad, wenn keine erweiterten Filter aktiv sind.
    """
    validate_pagination_or_error(limit, offset)
    normalized_climate = _normalize_climate_filter(climate)
    expanded_event_date_quality = _expand_event_date_quality_filter(event_date_quality)

    order_by_sql = _build_list_order_by_sql(sort_by, sort_dir)
    requested_filters = _build_requested_filters(
        country=country,
        climate=normalized_climate,
        vegetation=vegetation,
        elevation=elevation,
        temperature_band=temperature_band,
        precipitation_band=precipitation_band,
        soil_moisture_band=soil_moisture_band,
        ndvi_band=ndvi_band,
        humidity_band=humidity_band,
        pressure_band=pressure_band,
        light_pollution_band=light_pollution_band,
        slope_band=slope_band,
        water_distance_band=water_distance_band,
        human_impact_band=human_impact_band,
        landcover_group=landcover_group,
        coordinate_uncertainty_band=coordinate_uncertainty_band,
        soil_ph_band=soil_ph_band,
        soil_carbon_band=soil_carbon_band,
        worldclim_temp_band=worldclim_temp_band,
        worldclim_precip_band=worldclim_precip_band,
        event_date_quality=event_date_quality,
        basis_of_record_class=basis_of_record_class,
        taxon_resolution=taxon_resolution,
        media_coverage=media_coverage,
        license_class=license_class,
    )
    where_sql, params = _build_list_where_sql_and_params(
        q=q,
        requested_filters=requested_filters,
        elevation=elevation,
        expanded_event_date_quality=expanded_event_date_quality,
        observed_year=observed_year,
        has_image=has_image,
        bbox=bbox,
        compact=compact,
        offset=offset,
        raw_climate=climate,
        raw_vegetation=vegetation,
    )
    has_advanced_filters = _has_advanced_filters(requested_filters)
    rows, total, payload_builder = _fetch_list_rows_total_and_payload_builder(
        compact=compact,
        has_advanced_filters=has_advanced_filters,
        where_sql=where_sql,
        order_by_sql=order_by_sql,
        limit=limit,
        offset=offset,
        params=params,
        q=q,
        bbox=bbox,
        requested_filters=requested_filters,
        observed_year=observed_year,
        has_image=has_image,
        raw_climate=climate,
        raw_vegetation=vegetation,
    )

    page = (offset // limit) + 1
    return {
        "items": [payload_builder(dict(row)) for row in rows],
        "total": int(total),
        "page": page,
        "page_size": limit,
    }

def get_beetle_by_id_controller(beetle_id: str):
    """Liefert Detailinformationen zu einer bestimmten Kaefer-Beobachtung anhand ihrer ID, inklusive zugehoeriger Medien, in einem strukturierten Payload-Format."""
    entity_id = _parse_entity_id_or_error(beetle_id)

    row = fetch_beetle_detail_row_by_entity(entity_id)

    if row is None:
        raise_api_error(404, ERR.COMMON.NOT_FOUND, "Kein Eintrag fuer diese ID gefunden.")
    row = cast(Dict[str, Any], row)

    payload = to_beetle_payload(row)
    media_rows = []
    if row.get("source_type") == "manual":
        image_url = row.get("image_url_sample")
        if image_url:
            media_rows = [
                {
                    "image_url": image_url,
                    "license": row.get("license_sample"),
                    "creator": None,
                    "publisher": None,
                    "rights_holder": None,
                }
            ]
    elif row.get("gbif_id") is not None:
        media_rows = fetch_beetle_media_rows(int(row["gbif_id"]), limit=8)

    payload.setdefault("meta", {}).setdefault("media", {})["items"] = [
        {
            "url": item.get("image_url"),
            "license": item.get("license"),
            "creator": item.get("creator"),
            "publisher": item.get("publisher"),
            "rightsHolder": item.get("rights_holder"),
        }
        for item in media_rows
    ]
    if media_rows and not payload.get("imageUrl"):
        payload["imageUrl"] = media_rows[0].get("image_url")

    return payload

_COUNTRY_DETAIL_CACHE: "OrderedDict[str, Dict[str, Any]]" = OrderedDict()
_COUNTRY_DETAIL_CACHE_LOCK = Lock()
_COUNTRY_DETAIL_CACHE_MAX = 64


def clear_read_caches() -> None:
    """Leert die von diesem Modul verwalteten In-Memory-Read-Caches."""
    global ENV_RANGES_CACHE, ENV_RANGES_CACHE_TS
    with _COUNTRY_DETAIL_CACHE_LOCK:
        _COUNTRY_DETAIL_CACHE.clear()
    with _list_total_cache_lock:
        _list_total_cache.clear()
    ENV_RANGES_CACHE = None
    ENV_RANGES_CACHE_TS = None


def get_country_detail_controller(country_code: str):
    """Gibt aggregierte Laenderdetails fuer einen Laendercode zurueck. """
    normalized = country_code.strip().upper()
    if not normalized:
        raise_api_error(400, ERR.BEETLE.INVALID_COUNTRY_CODE, "Laendercode darf nicht leer sein.")

    with _COUNTRY_DETAIL_CACHE_LOCK:
        cached = _COUNTRY_DETAIL_CACHE.get(normalized)
        if cached is not None:
            _COUNTRY_DETAIL_CACHE.move_to_end(normalized)
            return cached

    candidates = country_filter_candidates(normalized)
    mapped = COUNTRY_CODE_TO_LOCATION_NAME.get(normalized)
    if mapped and mapped not in candidates:
        candidates.append(mapped)
    lookup_value = resolve_stored_country_value(candidates) or mapped or normalized

    overview, climates, vegetations, koppen, vegetation_zones, top_beetles = fetch_country_detail_rows(lookup_value)

    if overview is None or (overview.get("species_count") or 0) == 0:
        raise_api_error(404, ERR.COMMON.NOT_FOUND, "Keine Daten fuer diesen Laendercode gefunden.")
    overview = cast(Dict[str, Any], overview)

    observation_count = int(overview.get("observation_count") or 0)
    _list_finds = fetch_country_list_count(candidates)
    display_finds = _list_finds if _list_finds is not None else observation_count

    def _round_int(value):
        """Rundet auf eine ganze Zahl oder gibt None zurueck."""
        return int(round(value)) if value is not None else None

    def _share_rows(rows, key):
        """Baut Label + Fundzahl + Anteil je Zeile fuer Balken/Prozent."""
        out = []
        for row in rows:
            cnt = int(row["cnt"] or 0)
            out.append({
                key: row[key],
                "count": cnt,
                "share": round(cnt / observation_count, 4) if observation_count else None,
            })
        return out

    min_elev = overview.get("min_elevation")
    max_elev = overview.get("max_elevation")
    avg_temp = overview.get("avg_temperature")

    def _round_or_none(value, digits):
        """Rundet auf die angegebene Nachkommastellenzahl oder gibt None zurueck."""
        return round(float(value), digits) if value is not None else None

    def _metric_triplet(prefix, digits, as_int=False):
        """Liefert min/avg/max einer Metrik (as_int -> ganze Zahlen)."""
        rounder = _round_int if as_int else (lambda v: _round_or_none(v, digits))
        return {
            "min": rounder(overview.get("min_" + prefix)),
            "avg": rounder(overview.get("avg_" + prefix)),
            "max": rounder(overview.get("max_" + prefix)),
        }

    result = {
        "code": normalized,
        "name": ISO_TO_DISPLAY_NAME.get(normalized) or overview.get("country_name") or lookup_value,
        "speciesCount": int(overview.get("species_count") or 0),
        "observationCount": display_finds,
        "topClimates": [row["climate"] for row in climates],
        "topVegetations": [row["vegetation"] for row in vegetations],
        "elevationRange": [_round_int(min_elev), _round_int(max_elev)],
        "avgElevation": _round_int(overview.get("avg_elevation")),
        "avgTemperature": round(float(avg_temp), 1) if avg_temp is not None else None,
        "avgPrecipitation": _round_int(overview.get("avg_precipitation")),
        "avgSoilMoisture": (round(float(overview.get("avg_soil_moisture")), 3)
                            if overview.get("avg_soil_moisture") is not None else None),
        "avgNdvi": (round(float(overview.get("avg_ndvi")), 3)
                    if overview.get("avg_ndvi") is not None else None),
        "avgHumidity": (round(float(overview.get("avg_humidity")), 1)
                        if overview.get("avg_humidity") is not None else None),
        "avgSoilPh": (round(float(overview.get("avg_soil_ph")), 1)
                      if overview.get("avg_soil_ph") is not None else None),
        # Metriken je Umweltgroesse als min/avg/max (fuer die Balken im Panel):
        "metrics": {
            "elevation": _metric_triplet("elevation", 0, as_int=True),
            "temperature": _metric_triplet("temperature", 1),
            "precipitation": _metric_triplet("precipitation", 0, as_int=True),
            "soilMoisture": _metric_triplet("soil_moisture", 3),
            "ndvi": _metric_triplet("ndvi", 3),
            "humidity": _metric_triplet("humidity", 1),
            "soilPh": _metric_triplet("soil_ph", 1),
            "pressure": _metric_triplet("pressure", 0, as_int=True),
            "light": _metric_triplet("light", 2),
            "slope": _metric_triplet("slope", 1),
            "waterDistance": _metric_triplet("water_distance", 0, as_int=True),
            "humanModification": _metric_triplet("human_modification", 3),
        },
        "climates": _share_rows(climates, "climate"),
        "vegetations": _share_rows(vegetations, "vegetation"),
        # Feinere, vorberechnete Kartenzonen (Koeppen-Subtyp + Vegetationszone):
        "topKoppen": _share_rows(koppen, "koppen"),
        "topVegetationZones": _share_rows(vegetation_zones, "zone"),
        "topBeetles": [
            {
                "name": row["name"],
                "family": row["family"],
                "count": int(row["cnt"] or 0),
            }
            for row in top_beetles
        ],
    }

    with _COUNTRY_DETAIL_CACHE_LOCK:
        _COUNTRY_DETAIL_CACHE[normalized] = result
        _COUNTRY_DETAIL_CACHE.move_to_end(normalized)
        while len(_COUNTRY_DETAIL_CACHE) > _COUNTRY_DETAIL_CACHE_MAX:
            _COUNTRY_DETAIL_CACHE.popitem(last=False)

    return result

def get_beetle_media_controller(beetle_id: str, limit: int, offset: int):
    """Liefert eine paginierte Liste der Medien zu einer bestimmten Kaefer-Beobachtung (per ID) in einem strukturierten Format."""
    validate_pagination_or_error(limit, offset)

    entity_id = _parse_entity_id_or_error(beetle_id)
    detail_row = fetch_beetle_detail_row_by_entity(entity_id)
    if detail_row is None:
        raise_api_error(404, ERR.COMMON.NOT_FOUND, "Kein Eintrag fuer diese ID gefunden.")
    detail_row = cast(Dict[str, Any], detail_row)

    if detail_row.get("source_type") == "manual":
        record_id = detail_row.get("record_id")
        media_rows = fetch_beetle_record_media_rows(int(record_id)) if record_id is not None else []
        manual_items = [
            {
                "mediaId": f"manual-{row['media_id']}",
                "url": row.get("image_url"),
                "license": row.get("media_license"),
                "creator": row.get("media_creator"),
                "publisher": row.get("media_publisher"),
                "rightsHolder": row.get("media_rights_holder"),
                "references": row.get("media_references"),
            }
            for row in media_rows
            if row.get("image_url")
        ]

        page_items = manual_items[offset : offset + limit]
        page = (offset // limit) + 1
        return {
            "id": entity_id,
            "items": page_items,
            "total": len(manual_items),
            "page": page,
            "page_size": limit,
        }

    gbif_id_value = detail_row.get("gbif_id")
    if gbif_id_value is None:
        raise_api_error(404, ERR.COMMON.NOT_FOUND, "Kein Eintrag fuer diese ID gefunden.")

    gbif_id_text = str(gbif_id_value).strip()
    if not gbif_id_text or not gbif_id_text.isdigit():
        raise_api_error(404, ERR.COMMON.NOT_FOUND, "Kein Eintrag fuer diese ID gefunden.")

    gbif_id = int(gbif_id_text)

    rows, total = fetch_beetle_media_rows_total(gbif_id=gbif_id, limit=limit, offset=offset)

    page = (offset // limit) + 1
    return {
        "id": entity_id,
        "items": [
            {
                "mediaId": row.get("media_id"),
                "url": row.get("image_url"),
                "license": row.get("license"),
                "creator": row.get("creator"),
                "publisher": row.get("publisher"),
                "rightsHolder": row.get("rights_holder"),
                "references": row.get("references"),
            }
            for row in rows
        ],
        "total": total,
        "page": page,
        "page_size": limit,
    }


def get_environment_ranges_controller():
    """Gibt globale Min/Max-Wertebereiche fuer die Umwelt-Quicklook-Metriken zurueck."""
    cached = warm_environment_ranges_cache(force=False)
    return cached or warm_environment_ranges_cache(force=True) or {}


def get_featured_beetles_controller():
    """Liefert die Featured-Kaefer (echte rec-IDs + Name) als Quelle der Wahrheit
    fuer die Startseite, damit die statischen IDs nicht driften."""
    rows = fetch_featured_beetle_rows()
    items = [
        {
            "id": f"rec-{row['record_id']}",
            "name": row.get("scientific_name"),
            "family": row.get("family"),
            "precipitation": float(row["precipitation"]) if row.get("precipitation") is not None else None,
        }
        for row in rows
    ]
    return {"items": items, "total": len(items)}
