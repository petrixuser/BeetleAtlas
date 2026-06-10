# EXPLAIN Baseline (Sprint 1, Punkt 3)

Ziel: Die 2-3 teuersten Abfragen identifizieren, baseline messen und spaeter nach Indexen vergleichen.

## Vorgehen

1. Endpoint mit realistischem Request ausfuehren.
2. SQL aus Slow-Query-Log uebernehmen.
3. In MySQL mit `EXPLAIN FORMAT=JSON` analysieren.
4. Kernmetriken dokumentieren.

## Konfiguration

- `ENABLE_SLOW_QUERY_LOGGING=true`
- `SLOW_QUERY_MS=300` (zum Finden auch testweise `100`)

Messdatum: 2026-06-10 (DB befuellt, siehe `/stats/overview`)

## Kandidat A: GET /api/beetles

Beispielrequest:

```text
/api/beetles?limit=100&offset=0&sort_by=name&sort_dir=asc
```

EXPLAIN SQL:

```sql
EXPLAIN FORMAT=JSON
WITH latest_climate AS (...), media_agg AS (...)
SELECT ...
FROM observation o
JOIN beetle_species bs ON bs.beetle_id = o.beetle_id
JOIN location l ON l.location_id = o.location_id
LEFT JOIN media_agg ma ON ma.gbif_id = o.gbif_id
LEFT JOIN latest_climate lc ON lc.location_id = l.location_id AND lc.rn = 1
ORDER BY bs.scientific_name ASC
LIMIT 100 OFFSET 0;
```

Messwerte (Baseline):

- estimated_cost: `17241115.36`
- rows_examined_per_scan: `bs=1`, `o=20` (Join ueber `idx_observation_beetle_id`)
- used_indexes: `bs.idx_species_scientific_name`, `o.idx_observation_beetle_id`, `l.PRIMARY`, `m.idx_media_gbif_id`
- temp_table/filesort (ja/nein): `nein/nein` (Ordering ueber Species-Index)
- dauer_ms: `~582 ms` (`EXPLAIN ANALYZE`, Limit 100)

## Kandidat B: GET /api/map/points

Beispielrequest:

```text
/api/map/points?bbox=-81,-56,-34,13&zoom=7&limit=500&offset=0&sort_by=speciesName&sort_dir=asc
```

EXPLAIN SQL:

```sql
EXPLAIN FORMAT=JSON
WITH latest_climate AS (...)
SELECT ...
FROM observation o
JOIN beetle_species bs ON bs.beetle_id = o.beetle_id
JOIN location l ON l.location_id = o.location_id
LEFT JOIN latest_climate lc ON lc.location_id = l.location_id AND lc.rn = 1
WHERE l.longitude BETWEEN -81 AND -34
	AND l.latitude BETWEEN -56 AND 13
ORDER BY bs.scientific_name ASC
LIMIT 500 OFFSET 0;
```

Messwerte (Baseline):

- estimated_cost: `322672.44`
- rows_examined_per_scan: `l=92233` (Range auf Location), `o=1` (Ref auf `location_id`)
- used_indexes: `l.idx_location_lat_lon`, `o.idx_observation_location_id`, `bs.PRIMARY`
- temp_table/filesort (ja/nein): `ja/ja`
- dauer_ms: `~2633 ms` (`EXPLAIN ANALYZE`, Limit 500)

## Kandidat C: GET /observations

Beispielrequest:

```text
/observations?limit=100&offset=0&sort_by=event_date&sort_dir=desc
```

EXPLAIN SQL:

```sql
EXPLAIN FORMAT=JSON
SELECT
	o.gbif_id, o.beetle_id, o.location_id, o.event_date,
	o.dataset_name, o.image_available, bs.scientific_name
FROM observation o
JOIN beetle_species bs ON bs.beetle_id = o.beetle_id
ORDER BY o.event_date DESC
LIMIT 100 OFFSET 0;
```

Messwerte (Baseline):

- estimated_cost: `278336.73`
- rows_examined_per_scan: `o=100` (Index-Scan rueckwaerts), `bs=1`
- used_indexes: `o.idx_observation_event_date`, `bs.PRIMARY`
- temp_table/filesort (ja/nein): `nein/nein`
- dauer_ms: `~0.84 ms` (`EXPLAIN ANALYZE`, Limit 100)

## Kurzfazit Baseline

- Teuerster Kandidat ist aktuell `GET /api/map/points` (BBox + Sort), klar ueber 2.6s.
- `GET /api/beetles` liegt bei ~0.58s fuer Limit 100.
- `GET /observations` ist mit Event-Date-Index bereits sehr schnell.
- Fokus fuer Sprint 2: Index/Plan-Optimierung fuer B und danach A.

## Nach Sprint 2 (Vergleich)

Dieselben Abfragen erneut messen und in Tabelle gegenueberstellen.

Eingespielte Zusatzindizes in Sprint 2:

- `observation(location_id, beetle_id)` als `idx_observation_location_beetle`
- `location(longitude, latitude)` als `idx_location_lon_lat`
- `media(gbif_id, license)` als `idx_media_gbif_license`

Messdatum Nach-Index: 2026-06-10

Update (fachliche Korrektur):

- Query A wurde auf zeitlich korrekte Climate-Zuordnung umgestellt
	(`snapshot_date <= event_date`, dann `MAX(snapshot_date)`).
- Neue A-Messung mit dieser Logik: `~332 ms` (`EXPLAIN ANALYZE`, Limit 100).

| Query | Baseline ms | Nach Index ms | Delta | Kommentar |
|------|-------------:|--------------:|------:|-----------|
| A    | 582          | 332           | -250  | Fachlich korrekt (as-of event_date), trotzdem performant |
| B    | 2633         | 307           | -2326 | Deutlicher Gewinn; Plan nutzt Species-Indexpfad ohne Filesort |
| C    | 0.84         | 0.389         | -0.451| Weiterhin sehr schnell |

Kurzfazit nach Sprint 2:

- Hauptziel erreicht: Kandidat B ist von ~2.6s auf ~0.3s gefallen.
- Kandidat A ist nach fachlicher Korrektur (Climate as-of event_date) bei ~0.33s und damit im akzeptablen Bereich.
