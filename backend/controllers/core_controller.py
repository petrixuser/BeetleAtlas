"""Controller-Funktionen fuer Kernendpunkte: Healthcheck, Statistiken,
Arten- und Beobachtungslisten, Klimadaten sowie Datenqualitaets-Reports."""

from datetime import date
from typing import Dict, Optional
from datetime import datetime, timezone
import json

from fastapi import HTTPException
from backend.config.error_codes import ERR

from backend.repositories.core_repository import (
    fetch_climate_by_location,
    fetch_observations,
    fetch_quality_report_history_row,
    fetch_quality_report_history_rows,
    fetch_quality_report_rows,
    fetch_species,
    fetch_stats_overview_rows,
    insert_quality_report_history_snapshot,
    ping_db,
)

def raise_api_error(status_code: int, error: str, message: str) -> None:
    """Loest eine HTTPException mit Statuscode, Fehlertyp und Nachricht aus, fuer einheitliche Fehlerbehandlung in API-Controllern."""
    raise HTTPException(status_code=status_code, detail={"error": error, "message": message})

def validate_pagination_or_error(limit: int, offset: int, max_offset: int = 200000) -> None:
    """Prueft die aktuell in der Controller-Schicht erzwungenen Pagination-Grenzen.

    Prueft nur, dass offset max_offset nicht ueberschreitet.
    """
    if offset > max_offset:
        raise_api_error(400, ERR.CORE.INVALID_PAGINATION, f"offset muss <= {max_offset} sein")

def resolve_order_clause_or_error(sort_by: str, sort_dir: str, allowed_columns: Dict[str, str]) -> str:
    """Baut eine sichere ORDER-BY-Klausel aus einer Allowlist sortierbarer Spalten.

    Loest einen API-Fehler aus, wenn sort_by nicht in allowed_columns enthalten ist.
    """
    column = allowed_columns.get(sort_by)
    if column is None:
        raise_api_error(400, ERR.CORE.INVALID_SORT, f"sort_by muss einer von: {', '.join(allowed_columns.keys())} sein")

    direction = "ASC" if sort_dir == "asc" else "DESC"
    return f"{column} {direction}"

def parse_bbox_or_error(bbox: str) -> Dict[str, float]:
    """Parst einen Bounding-Box-String im Format "minLng,minLat,maxLng,maxLat" und gibt ein Dict mit den entsprechenden Float-Werten zurueck. Loest einen API-Fehler bei ungueltiger Eingabe aus."""
    parts = [p.strip() for p in bbox.split(",")]
    if len(parts) != 4:
        raise_api_error(400, ERR.CORE.INVALID_BBOX, "bbox muss minLng,minLat,maxLng,maxLat sein")

    try:
        min_lng, min_lat, max_lng, max_lat = [float(p) for p in parts]
    except ValueError:
        raise_api_error(400, ERR.CORE.INVALID_BBOX, "bbox muss numerische Werte enthalten")

    if min_lng >= max_lng or min_lat >= max_lat:
        raise_api_error(400, ERR.CORE.INVALID_BBOX, "bbox-Minwerte muessen kleiner als die Maxwerte sein")

    return {
        "min_lng": min_lng,
        "min_lat": min_lat,
        "max_lng": max_lng,
        "max_lat": max_lat,
    }

def healthcheck_controller():
    """Prueft die Datenbankverbindung und gibt eine Statusmeldung zurueck, ob die API gesund ist."""
    ping_db()
    return {"status": "ok"}

def stats_overview_controller():
    """Liefert eine Uebersicht der Statistiken zu Kaefer-Beobachtungen, Arten und Klima-Snapshots in strukturierter Form."""
    rows = fetch_stats_overview_rows()
    return {"tables": rows}

def list_species_controller(limit: int, offset: int, sort_by: str, sort_dir: str):
    """Liefert eine paginierte Liste der Kaefer-Arten anhand der uebergebenen Parameter (inkl. Sortieroptionen) in strukturierter Form."""
    validate_pagination_or_error(limit, offset)
    order_by_sql = resolve_order_clause_or_error(
        sort_by,
        sort_dir,
        {
            "beetle_id": "beetle_id",
            "scientific_name": "scientific_name",
            "family": "family",
        },
    )

    rows, total = fetch_species(limit, offset, order_by_sql)
    return {
        "items": rows,
        "total": total,
        "page": (offset // limit) + 1,
        "page_size": limit,
    }

def list_observations_controller(
    beetle_id: Optional[int],
    year: Optional[int],
    has_image: Optional[bool],
    limit: int,
    offset: int,
    sort_by: str,
    sort_dir: str,
):
    """Liefert eine Liste von Kaefer-Beobachtungen anhand verschiedener Filterparameter, inklusive Pagination und Sortierung, in strukturierter Form."""
    validate_pagination_or_error(limit, offset)

    order_by_sql = resolve_order_clause_or_error(
        sort_by,
        sort_dir,
        {
            "gbif_id": "o.gbif_id",
            "event_date": "o.event_date",
            "beetle_id": "o.beetle_id",
        },
    )

    rows, total = fetch_observations(
        beetle_id=beetle_id,
        year=year,
        has_image=has_image,
        limit=limit,
        offset=offset,
        order_by_sql=order_by_sql,
    )

    return {
        "items": rows,
        "total": total,
        "page": (offset // limit) + 1,
        "page_size": limit,
    }

def climate_by_location_controller(
    location_id: int,
    from_date: Optional[date],
    to_date: Optional[date],
    limit: int,
):
    """Liefert Klimadaten fuer einen bestimmten Standort anhand der location_id und eines optionalen Datumsbereichs in strukturierter Form."""
    rows = fetch_climate_by_location(
        location_id=location_id,
        from_date=from_date,
        to_date=to_date,
        limit=limit,
    )
    return {"location_id": location_id, "items": rows}

def quality_report_controller():
    """Erstellt einen Qualitaetsreport anhand verschiedener Metriken zu Kaefer-Beobachtungen, Standorten und Klima-Snapshots und gibt ihn strukturiert zurueck."""
    totals, observation_nulls, location_nulls, snapshot_nulls, ee_coverage = fetch_quality_report_rows()

    return build_quality_report_payload(
        totals=totals,
        observation_nulls=observation_nulls,
        location_nulls=location_nulls,
        snapshot_nulls=snapshot_nulls,
        ee_coverage=ee_coverage,
    )

def build_quality_report_payload(*, totals, observation_nulls, location_nulls, snapshot_nulls, ee_coverage):
    """Baut das Qualitaetsreport-API-Payload aus den aggregierten Metrik-Zeilen.

    Berechnet Null-Rate-Prozentwerte und die EE-Snapshot-Abdeckung.
    """
    def to_rate_items(row, total):
        """Wandelt eine Null-Count-Zeile in Feld-Items mit missing-Anzahl und ratePct um."""
        items = []
        denominator = max(int(total or 0), 1)
        for key, value in row.items():
            missing = int(value or 0)
            field = key.replace("_missing", "")
            items.append(
                {
                    "field": field,
                    "missing": missing,
                    "ratePct": round((missing / denominator) * 100.0, 3),
                }
            )
        return items

    observation_total = int(totals.get("observation_count") or 0)
    location_total = int(totals.get("location_count") or 0)
    snapshot_total = int(totals.get("climate_snapshot_count") or 0)

    with_snapshot = int(ee_coverage.get("with_snapshot_match") or 0)
    without_snapshot = max(observation_total - with_snapshot, 0)
    coverage_rate = round((with_snapshot / max(observation_total, 1)) * 100.0, 3)

    return {
        "generatedAt": datetime.now(timezone.utc).isoformat(),
        "totals": {
            "observations": observation_total,
            "locations": location_total,
            "climateSnapshots": snapshot_total,
        },
        "observationNullRates": to_rate_items(observation_nulls, observation_total),
        "locationNullRates": to_rate_items(location_nulls, location_total),
        "climateSnapshotNullRates": to_rate_items(snapshot_nulls, snapshot_total),
        "eeCoverage": {
            "withSnapshotMatch": with_snapshot,
            "withoutSnapshotMatch": without_snapshot,
            "withSnapshotRatePct": coverage_rate,
        },
    }

def create_quality_report_snapshot_controller(source: Optional[str]):
    """Erstellt und persistiert einen neuen Qualitaetsreport-Snapshot.

    Gibt die erzeugte Snapshot-ID zusammen mit dem generierten Report-Payload zurueck.
    """
    report = quality_report_controller()
    snapshot_id = insert_quality_report_history_snapshot(
        source_label=source,
        observation_count=report["totals"]["observations"],
        location_count=report["totals"]["locations"],
        climate_snapshot_count=report["totals"]["climateSnapshots"],
        observation_null_rates=report["observationNullRates"],
        location_null_rates=report["locationNullRates"],
        climate_snapshot_null_rates=report["climateSnapshotNullRates"],
        ee_coverage=report["eeCoverage"],
    )

    return {
        "snapshotId": snapshot_id,
        "source": source,
        "report": report,
    }

def list_quality_report_history_controller(limit: int, offset: int):
    """Liefert eine Liste von Qualitaetsreport-Snapshots aus der Datenbank anhand der Pagination-Parameter in strukturierter Form."""
    validate_pagination_or_error(limit, offset)

    rows, total = fetch_quality_report_history_rows(limit=limit, offset=offset)

    items = []
    for row in rows:
        items.append(_history_row_to_payload(dict(row)))

    return {
        "items": items,
        "total": total,
        "page": (offset // limit) + 1,
        "page_size": limit,
    }

def compare_quality_report_history_controller(from_id: int, to_id: int):
    """Vergleicht zwei Qualitaetsreport-Snapshots anhand ihrer IDs, berechnet die Deltas verschiedener Metriken und gibt das Vergleichsergebnis strukturiert zurueck."""
    from_row = fetch_quality_report_history_row(from_id)
    to_row = fetch_quality_report_history_row(to_id)

    if from_row is None:
        raise_api_error(404, ERR.COMMON.NOT_FOUND, f"Qualitaets-Snapshot mit ID {from_id} wurde nicht gefunden")
    if to_row is None:
        raise_api_error(404, ERR.COMMON.NOT_FOUND, f"Qualitaets-Snapshot mit ID {to_id} wurde nicht gefunden")

    from_payload = _history_row_to_payload(from_row)
    to_payload = _history_row_to_payload(to_row)

    ee_from = from_payload["eeCoverage"]
    ee_to = to_payload["eeCoverage"]

    return {
        "fromSnapshot": {
            "snapshotId": from_payload["snapshotId"],
            "generatedAt": from_payload["generatedAt"],
            "source": from_payload["source"],
        },
        "toSnapshot": {
            "snapshotId": to_payload["snapshotId"],
            "generatedAt": to_payload["generatedAt"],
            "source": to_payload["source"],
        },
        "observationNullRateDelta": _build_delta_items(
            from_payload["observationNullRates"],
            to_payload["observationNullRates"],
        ),
        "locationNullRateDelta": _build_delta_items(
            from_payload["locationNullRates"],
            to_payload["locationNullRates"],
        ),
        "climateSnapshotNullRateDelta": _build_delta_items(
            from_payload["climateSnapshotNullRates"],
            to_payload["climateSnapshotNullRates"],
        ),
        "eeCoverageDelta": {
            "withSnapshotMatchDelta": int(ee_to["withSnapshotMatch"]) - int(ee_from["withSnapshotMatch"]),
            "withoutSnapshotMatchDelta": int(ee_to["withoutSnapshotMatch"]) - int(ee_from["withoutSnapshotMatch"]),
            "withSnapshotRatePctDelta": round(
                float(ee_to["withSnapshotRatePct"]) - float(ee_from["withSnapshotRatePct"]),
                3,
            ),
        },
    }

def _to_field_map(items):
    """Baut ein nach "field" indiziertes Dict fuer schnelle Feld-Lookups in Delta-Berechnungen."""
    return {item["field"]: item for item in items}

def _build_delta_items(from_items, to_items):
    """Berechnet feldweise Deltas zwischen zwei Null-Rate-Listen (to - from) fuer missing-Anzahl und ratePct. Fehlende Felder auf einer Seite werden als 0 behandelt, damit Vergleiche robust bleiben."""
    from_map = _to_field_map(from_items)
    to_map = _to_field_map(to_items)
    fields = sorted(set(from_map.keys()) | set(to_map.keys()))
    deltas = []
    for field in fields:
        prev = from_map.get(field, {"missing": 0, "ratePct": 0.0})
        curr = to_map.get(field, {"missing": 0, "ratePct": 0.0})
        deltas.append(
            {
                "field": field,
                "missingDelta": int(curr["missing"]) - int(prev["missing"]),
                "ratePctDelta": round(float(curr["ratePct"]) - float(prev["ratePct"]), 3),
            }
        )
    return deltas


def _parse_json_or_value(value):
    """Hilfsfunktion, die JSON-Strings parst oder den Wert unveraendert zurueckgibt, falls er bereits ein dict oder list ist; genutzt beim Verarbeiten der Qualitaetsreport-Historie."""
    if isinstance(value, (dict, list)):
        return value
    if value is None:
        return None
    if isinstance(value, str):
        return json.loads(value)
    return value


def _history_row_to_payload(row: dict):
    """Wandelt eine Datenbankzeile eines Qualitaetsreport-Snapshots in ein strukturiertes Payload-Format fuer API-Antworten um."""
    observation_null_rates = _parse_json_or_value(row.get("observation_null_rates_json"))
    location_null_rates = _parse_json_or_value(row.get("location_null_rates_json"))
    climate_snapshot_null_rates = _parse_json_or_value(row.get("climate_snapshot_null_rates_json"))
    ee_coverage = _parse_json_or_value(row.get("ee_coverage_json"))

    if not isinstance(observation_null_rates, list):
        observation_null_rates = []
    if not isinstance(location_null_rates, list):
        location_null_rates = []
    if not isinstance(climate_snapshot_null_rates, list):
        climate_snapshot_null_rates = []
    if not isinstance(ee_coverage, dict):
        ee_coverage = {}

    return {
        "snapshotId": int(row["quality_report_id"]),
        "generatedAt": row["generated_at"].isoformat() if row.get("generated_at") is not None else None,
        "source": row.get("source_label"),
        "totals": {
            "observations": int(row.get("observation_count") or 0),
            "locations": int(row.get("location_count") or 0),
            "climateSnapshots": int(row.get("climate_snapshot_count") or 0),
        },
        "observationNullRates": observation_null_rates,
        "locationNullRates": location_null_rates,
        "climateSnapshotNullRates": climate_snapshot_null_rates,
        "eeCoverage": ee_coverage,
    }
