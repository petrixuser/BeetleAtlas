#!/usr/bin/env python3
"""Vorberechnung der Klima- und Vegetationszonen pro Fundort (location).

Fuer jeden Standort wird per Punkt-in-Polygon-Test bestimmt, in welcher
Koeppen-Geiger-Klimazone (z. B. ``Af``) und in welcher Vegetations-/Oekoregion
(z. B. ``Tropischer Regenwald``) er liegt. Grundlage sind exakt dieselben
GeoJSON-Polygone, die auch die Karte im Frontend anzeigt
(``frontend/assets/koppen-latam.geojson`` und ``ecoregions-latam.geojson``).

"""

from __future__ import annotations

import json
import math
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pymysql

# ---------------------------------------------------------------------------
# Konfiguration
# ---------------------------------------------------------------------------

REPO_ROOT = Path(__file__).resolve().parents[2]
ASSETS_DIR = REPO_ROOT / "frontend" / "assets"
KOPPEN_FILE = ASSETS_DIR / "koppen-latam.geojson"
ECOREGION_FILE = ASSETS_DIR / "ecoregions-latam.geojson"
COUNTRY_FILE = ASSETS_DIR / "latin-america-countries.js"

GRID_SIZE_DEG = 0.5

BATCH_SIZE = 5000

Ring = List[Tuple[float, float]]       
Polygon = List[Ring]                  
BBox = Tuple[float, float, float, float]  


def db_config() -> Dict[str, object]:
    """Liest die DB-Verbindungsparameter aus den Umgebungsvariablen."""
    return {
        "host": os.getenv("DB_HOST", "127.0.0.1"),
        "port": int(os.getenv("DB_PORT", "3306")),
        "user": os.getenv("DB_USER", "beetle_app"),
        "password": os.getenv("DB_PASSWORD", "beetleapp123"),
        "database": os.getenv("DB_NAME", "beetle_db"),
        "charset": "utf8mb4",
    }


# ---------------------------------------------------------------------------
# GeoJSON laden und Geometrie normalisieren
# ---------------------------------------------------------------------------

def _rings_from_polygon(coords: List) -> Polygon:
    """GeoJSON-Polygon-Koordinaten in Ring-Listen [(lng, lat), ...] wandeln."""
    rings: Polygon = []
    for ring in coords:
        pts: Ring = [(float(pt[0]), float(pt[1])) for pt in ring if len(pt) >= 2]
        if len(pts) >= 3:
            rings.append(pts)
    return rings


def _polygons_from_geometry(geometry: dict) -> List[Polygon]:
    """Liefert eine Liste von Polygonen (je Polygon: aussen + Loecher)."""
    if not geometry:
        return []
    gtype = geometry.get("type")
    coords = geometry.get("coordinates")
    if gtype == "Polygon":
        rings = _rings_from_polygon(coords)
        return [rings] if rings else []
    if gtype == "MultiPolygon":
        result: List[Polygon] = []
        for poly in coords:
            rings = _rings_from_polygon(poly)
            if rings:
                result.append(rings)
        return result
    return []


def _bbox_of_polygon(polygon: Polygon) -> Optional[BBox]:
    """Berechnet die Bounding-Box (min_lng, min_lat, max_lng, max_lat) eines Polygons."""
    min_lng = min_lat = math.inf
    max_lng = max_lat = -math.inf
    for lng, lat in polygon[0]:
        if lng < min_lng:
            min_lng = lng
        if lng > max_lng:
            max_lng = lng
        if lat < min_lat:
            min_lat = lat
        if lat > max_lat:
            max_lat = lat
    if not math.isfinite(min_lng):
        return None
    return (min_lng, min_lat, max_lng, max_lat)


class ZoneIndex:
    """Raeumlicher Grid-Index fuer schnelle Punkt-in-Polygon-Abfragen."""

    def __init__(self, grid_size: float = GRID_SIZE_DEG) -> None:
        self.grid_size = grid_size
        # (poly, value) Eintraege
        self._entries: List[Tuple[Polygon, str]] = []
        self._entry_bbox: List[BBox] = []
        self._grid: Dict[Tuple[int, int], List[int]] = {}

    def _cell(self, lng: float, lat: float) -> Tuple[int, int]:
        """Berechnet die Rasterzelle (cx, cy) fuer einen Punkt."""
        return (int(math.floor(lng / self.grid_size)), int(math.floor(lat / self.grid_size)))

    def add_feature(self, geometry: dict, value: str) -> None:
        """Fuegt ein GeoJSON-Feature (Polygon/MultiPolygon) mit zugehoerigem Wert hinzu."""
        if not value:
            return
        for polygon in _polygons_from_geometry(geometry):
            bbox = _bbox_of_polygon(polygon)
            if bbox is None:
                continue
            idx = len(self._entries)
            self._entries.append((polygon, value))
            self._entry_bbox.append(bbox)
            min_lng, min_lat, max_lng, max_lat = bbox
            cx0, cy0 = self._cell(min_lng, min_lat)
            cx1, cy1 = self._cell(max_lng, max_lat)
            for cx in range(cx0, cx1 + 1):
                for cy in range(cy0, cy1 + 1):
                    self._grid.setdefault((cx, cy), []).append(idx)

    @staticmethod
    def _ring_contains(lng: float, lat: float, ring: Ring) -> bool:
        """Ray-Casting-Test – identisch zur Frontend-Kartenlogik."""
        inside = False
        n = len(ring)
        j = n - 1
        for i in range(n):
            xi, yi = ring[i]
            xj, yj = ring[j]
            if ((yi > lat) != (yj > lat)) and (
                lng < (xj - xi) * (lat - yi) / ((yj - yi) or 1e-12) + xi
            ):
                inside = not inside
            j = i
        return inside

    def _polygon_contains(self, lng: float, lat: float, polygon: Polygon) -> bool:
        """Prueft, ob ein Punkt innerhalb eines Polygons (mit Loechern) liegt."""
        if not self._ring_contains(lng, lat, polygon[0]):
            return False
        for hole in polygon[1:]:
            if self._ring_contains(lng, lat, hole):
                return False
        return True

    def classify(self, lng: float, lat: float) -> Optional[str]:
        """Gibt den Wert der ersten Polygon-Feature zurueck, das den Punkt enthaelt."""
        candidates = self._grid.get(self._cell(lng, lat))
        if not candidates:
            return None
        for idx in candidates:
            min_lng, min_lat, max_lng, max_lat = self._entry_bbox[idx]
            if lng < min_lng or lng > max_lng or lat < min_lat or lat > max_lat:
                continue
            polygon, value = self._entries[idx]
            if self._polygon_contains(lng, lat, polygon):
                return value
        return None


def build_index(path: Path, value_key: str) -> ZoneIndex:
    """Laedt die GeoJSON-Datei und baut den ZoneIndex auf."""
    print(f">> Lade {path.name} ...", flush=True)
    with path.open(encoding="utf-8") as fh:
        data = json.load(fh)
    index = ZoneIndex()
    features = data.get("features", [])
    for feat in features:
        props = feat.get("properties") or {}
        value = props.get(value_key)
        if value is None:
            continue
        index.add_feature(feat.get("geometry"), str(value))
    print(f"   {len(features)} Features indiziert.", flush=True)
    return index


def build_country_index(path: Path, value_key: str = "name") -> ZoneIndex:
    """Laedt die als JS gewrappte Laender-GeoJSON (window.X = {...};)."""
    print(f">> Lade {path.name} ...", flush=True)
    raw = path.read_text(encoding="utf-8").strip()
    start = raw.find("{")
    end = raw.rfind("}")
    if start < 0 or end < 0:
        print("   WARN: keine GeoJSON gefunden.", flush=True)
        return ZoneIndex()
    data = json.loads(raw[start : end + 1])
    index = ZoneIndex()
    features = data.get("features", [])
    for feat in features:
        props = feat.get("properties") or {}
        value = props.get(value_key)
        if value is None:
            continue
        index.add_feature(feat.get("geometry"), str(value))
    print(f"   {len(features)} Laender indiziert.", flush=True)
    return index


# ---------------------------------------------------------------------------
# Datenbank-Schema sicherstellen
# ---------------------------------------------------------------------------

def _column_exists(cur, table: str, column: str) -> bool:
    """Prueft, ob eine Spalte in einer Tabelle existiert."""
    cur.execute(
        """
        SELECT 1 FROM information_schema.columns
        WHERE table_schema = DATABASE() AND table_name = %s AND column_name = %s
        """,
        (table, column),
    )
    return cur.fetchone() is not None


def _index_exists(cur, table: str, index: str) -> bool:
    """Prueft, ob ein Index in einer Tabelle existiert."""
    cur.execute(
        """
        SELECT 1 FROM information_schema.statistics
        WHERE table_schema = DATABASE() AND table_name = %s AND index_name = %s
        """,
        (table, index),
    )
    return cur.fetchone() is not None


def ensure_schema(cur) -> None:
    """Fuegt koppen_code / vegetation_zone Spalten + Indizes idempotent hinzu."""
    specs = [
        ("location", "koppen_code", "VARCHAR(8) NULL"),
        ("location", "vegetation_zone", "VARCHAR(80) NULL"),
        ("location", "country_derived", "VARCHAR(255) NULL"),
        ("map_point_read", "koppen_code", "VARCHAR(8) NULL"),
        ("map_point_read", "vegetation_zone", "VARCHAR(80) NULL"),
        ("beetle_list_read", "koppen_code", "VARCHAR(8) NULL"),
        ("beetle_list_read", "vegetation_zone", "VARCHAR(80) NULL"),
    ]
    for table, column, coltype in specs:
        if not _column_exists(cur, table, column):
            print(f">> ALTER {table} ADD {column}", flush=True)
            cur.execute(f"ALTER TABLE {table} ADD COLUMN {column} {coltype}")

    indexes = [
        ("map_point_read", "idx_mpr_koppen_bbox", "(koppen_code, lng, lat)"),
        ("map_point_read", "idx_mpr_vegzone_bbox", "(vegetation_zone, lng, lat)"),
        ("beetle_list_read", "idx_blr_koppen_entity", "(koppen_code, entity_id)"),
        ("beetle_list_read", "idx_blr_vegzone_entity", "(vegetation_zone, entity_id)"),
    ]
    for table, index, cols in indexes:
        if not _index_exists(cur, table, index):
            print(f">> CREATE INDEX {index} ON {table}", flush=True)
            cur.execute(f"CREATE INDEX {index} ON {table} {cols}")


# ---------------------------------------------------------------------------
# Hauptlogik
# ---------------------------------------------------------------------------

def precompute_locations(conn, koppen: ZoneIndex, eco: ZoneIndex, country: ZoneIndex) -> None:
    """Berechnet Koeppen-/Vegetations-/Land-Zonen fuer alle Standorte und schreibt sie in location."""
    read_cur = conn.cursor()
    read_cur.execute(
        "SELECT location_id, latitude, longitude FROM location "
        "WHERE latitude IS NOT NULL AND longitude IS NOT NULL"
    )

    write_cur = conn.cursor()
    write_cur.execute("DROP TEMPORARY TABLE IF EXISTS tmp_zone")
    write_cur.execute(
        "CREATE TEMPORARY TABLE tmp_zone ("
        "location_id INT PRIMARY KEY, koppen_code VARCHAR(8) NULL, "
        "vegetation_zone VARCHAR(80) NULL, country_derived VARCHAR(255) NULL) ENGINE=InnoDB"
    )

    batch: List[Tuple[int, Optional[str], Optional[str], Optional[str]]] = []
    processed = 0
    matched_koppen = 0
    matched_eco = 0
    matched_country = 0
    started = time.time()

    def flush() -> None:
        """Schreibt den aktuellen Batch in die temporaere Tabelle tmp_zone."""
        if not batch:
            return
        write_cur.executemany(
            "INSERT INTO tmp_zone (location_id, koppen_code, vegetation_zone, country_derived) "
            "VALUES (%s, %s, %s, %s)",
            batch,
        )
        batch.clear()

    for location_id, lat, lng in read_cur:
        latf = float(lat)
        lngf = float(lng)
        kc = koppen.classify(lngf, latf)
        vz = eco.classify(lngf, latf)
        cd = country.classify(lngf, latf)
        if kc:
            matched_koppen += 1
        if vz:
            matched_eco += 1
        if cd:
            matched_country += 1
        batch.append((location_id, kc, vz, cd))
        processed += 1
        if len(batch) >= BATCH_SIZE:
            flush()
        if processed % 50000 == 0:
            rate = processed / max(time.time() - started, 1e-6)
            print(f"   {processed} Standorte klassifiziert ({rate:.0f}/s) ...", flush=True)

    flush()
    read_cur.close()

    print(
        f">> {processed} Standorte verarbeitet | "
        f"Koeppen-Treffer: {matched_koppen} | Vegetations-Treffer: {matched_eco} | "
        f"Land-Treffer: {matched_country}",
        flush=True,
    )

    print(">> Schreibe location.koppen_code / vegetation_zone / country_derived ...", flush=True)
    write_cur.execute(
        "UPDATE location l JOIN tmp_zone t ON l.location_id = t.location_id "
        "SET l.koppen_code = t.koppen_code, l.vegetation_zone = t.vegetation_zone, "
        "l.country_derived = t.country_derived"
    )
    write_cur.execute("DROP TEMPORARY TABLE IF EXISTS tmp_zone")
    write_cur.close()
    conn.commit()


def propagate_to_read_models(conn) -> None:
    """Kopiert die berechneten Zonen aus location in die Read-Modelle map_point_read und beetle_list_read."""
    cur = conn.cursor()
    print(">> Uebertrage Zonen in map_point_read ...", flush=True)
    cur.execute(
        "UPDATE map_point_read m "
        "JOIN observation o ON o.gbif_id = m.gbif_id AND m.source_type = 'observation' "
        "JOIN location l ON l.location_id = o.location_id "
        "SET m.koppen_code = l.koppen_code, m.vegetation_zone = l.vegetation_zone, "
        "m.country = COALESCE(l.country_derived, m.country)"
    )
    print(">> Uebertrage Zonen in beetle_list_read ...", flush=True)
    cur.execute(
        "UPDATE beetle_list_read e "
        "JOIN map_point_read m ON m.entity_id = e.entity_id "
        "SET e.koppen_code = m.koppen_code, e.vegetation_zone = m.vegetation_zone, "
        "e.country = m.country"
    )
    cur.close()
    conn.commit()


def report(conn) -> None:
    """Erzeugt eine kurze Statistik der Top-Koeppen- und Vegetationszonen in map_point_read."""
    cur = conn.cursor()
    cur.execute(
        "SELECT koppen_code, COUNT(*) c FROM map_point_read "
        "GROUP BY koppen_code ORDER BY c DESC LIMIT 8"
    )
    print(">> Top Koeppen-Zonen (map_point_read):", flush=True)
    for code, cnt in cur.fetchall():
        print(f"     {code!s:<10} {cnt}", flush=True)
    cur.execute(
        "SELECT vegetation_zone, COUNT(*) c FROM map_point_read "
        "GROUP BY vegetation_zone ORDER BY c DESC LIMIT 8"
    )
    print(">> Top Vegetationszonen (map_point_read):", flush=True)
    for zone, cnt in cur.fetchall():
        print(f"     {zone!s:<30} {cnt}", flush=True)
    cur.close()


def main() -> int:
    """Baut die Zonen-Indizes auf und schreibt die Zonen in location und die Read-Modelle."""
    if not KOPPEN_FILE.exists() or not ECOREGION_FILE.exists():
        print("FEHLER: GeoJSON-Dateien nicht gefunden unter", ASSETS_DIR, file=sys.stderr)
        return 1

    koppen = build_index(KOPPEN_FILE, "code")
    eco = build_index(ECOREGION_FILE, "name")
    country = build_country_index(COUNTRY_FILE) if COUNTRY_FILE.exists() else ZoneIndex()

    conn = pymysql.connect(**db_config())
    try:
        with conn.cursor() as cur:
            ensure_schema(cur)
        conn.commit()

        precompute_locations(conn, koppen, eco, country)
        propagate_to_read_models(conn)
        report(conn)
    finally:
        conn.close()

    print(">> FERTIG", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
