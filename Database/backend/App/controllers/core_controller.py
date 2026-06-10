from datetime import date
from typing import Dict, Optional
from datetime import datetime, timezone
import json

from fastapi import HTTPException

from Database.Backend.App.repositories.core_repository import (
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
    raise HTTPException(status_code=status_code, detail={"error": error, "message": message})


def validate_pagination_or_error(limit: int, offset: int, max_offset: int = 200000) -> None:
    if offset > max_offset:
        raise_api_error(400, "invalid_pagination", f"offset must be <= {max_offset}")


def resolve_order_clause_or_error(sort_by: str, sort_dir: str, allowed_columns: Dict[str, str]) -> str:
    column = allowed_columns.get(sort_by)
    if column is None:
        raise_api_error(400, "invalid_sort", f"sort_by must be one of: {', '.join(allowed_columns.keys())}")

    direction = "ASC" if sort_dir == "asc" else "DESC"
    return f"{column} {direction}"


def parse_bbox_or_error(bbox: str) -> Dict[str, float]:
    parts = [p.strip() for p in bbox.split(",")]
    if len(parts) != 4:
        raise_api_error(400, "invalid_bbox", "bbox must be minLng,minLat,maxLng,maxLat")

    try:
        min_lng, min_lat, max_lng, max_lat = [float(p) for p in parts]
    except ValueError:
        raise_api_error(400, "invalid_bbox", "bbox must contain numeric values")

    if min_lng >= max_lng or min_lat >= max_lat:
        raise_api_error(400, "invalid_bbox", "bbox min values must be smaller than max values")

    return {
        "min_lng": min_lng,
        "min_lat": min_lat,
        "max_lng": max_lng,
        "max_lat": max_lat,
    }

def healthcheck_controller():
    ping_db()
    return {"status": "ok"}


def stats_overview_controller():
    rows = fetch_stats_overview_rows()
    return {"tables": rows}


def list_species_controller(limit: int, offset: int, sort_by: str, sort_dir: str):
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
    rows = fetch_climate_by_location(
        location_id=location_id,
        from_date=from_date,
        to_date=to_date,
        limit=limit,
    )
    return {"location_id": location_id, "items": rows}


def quality_report_controller():
    totals, observation_nulls, location_nulls, snapshot_nulls, ee_coverage = fetch_quality_report_rows()

    return build_quality_report_payload(
        totals=totals,
        observation_nulls=observation_nulls,
        location_nulls=location_nulls,
        snapshot_nulls=snapshot_nulls,
        ee_coverage=ee_coverage,
    )


def build_quality_report_payload(*, totals, observation_nulls, location_nulls, snapshot_nulls, ee_coverage):
    def to_rate_items(row, total):
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
    from_row = fetch_quality_report_history_row(from_id)
    to_row = fetch_quality_report_history_row(to_id)

    if from_row is None:
        raise_api_error(404, "not_found", f"Quality snapshot with id {from_id} was not found")
    if to_row is None:
        raise_api_error(404, "not_found", f"Quality snapshot with id {to_id} was not found")

    from_payload = _history_row_to_payload(from_row)
    to_payload = _history_row_to_payload(to_row)

    def to_field_map(items):
        return {item["field"]: item for item in items}

    def build_delta_items(from_items, to_items):
        from_map = to_field_map(from_items)
        to_map = to_field_map(to_items)
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
        "observationNullRateDelta": build_delta_items(
            from_payload["observationNullRates"],
            to_payload["observationNullRates"],
        ),
        "locationNullRateDelta": build_delta_items(
            from_payload["locationNullRates"],
            to_payload["locationNullRates"],
        ),
        "climateSnapshotNullRateDelta": build_delta_items(
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


def _parse_json_or_value(value):
    if isinstance(value, (dict, list)):
        return value
    if value is None:
        return None
    if isinstance(value, str):
        return json.loads(value)
    return value


def _history_row_to_payload(row: dict):
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
