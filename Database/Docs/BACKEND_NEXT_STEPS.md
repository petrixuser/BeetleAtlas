## Backend Next Steps (Stand 2026-06-10)

Dieses Dokument ist der aktuelle Ist-/Soll-Stand fuer Backend + Datenbank.

## Was bereits fertig ist

### Sprint 1 bis 5 (abgeschlossen)
1. Stabilisierung, Messbarkeit und Logging sind umgesetzt.
2. Performance-Basis (Indizes + EXPLAIN-Vergleiche) ist vorhanden.
3. Schichtenarchitektur (Router/Controller/Repository) ist eingefuehrt.
4. Docker-Betrieb ist reproduzierbar dokumentiert.
5. API-Vertragstests, OpenAPI-Beispiele und Quality-Report sind vorhanden.

### Sprint 6 (abgeschlossen)
1. Event-Date Normalisierung:
- `event_date_parsed` inkl. Backfill + Index.
- umgesetzt in:
	- `Database/Backend/SQL/DatabseShema.sql`
	- `Database/Backend/SQL/LoadGBIFCSVToDB.sql`
	- `Database/Backend/SQL/MigrateObservationEventDateParsed.sql`

2. Medienlieferung produktiv:
- Bildfelder in Liste/Detail.
- eigener Endpunkt `GET /api/beetles/{id}/media`.
- umgesetzt in:
	- `Database/Backend/App/repositories/beetle_repository.py`
	- `Database/Backend/App/controllers/beetle_controller.py`
	- `Database/Backend/App/routers/beetle_router.py`

3. Medien-Performance:
- Index `media (gbif_id, media_id)`.
- umgesetzt in:
	- `Database/Backend/SQL/MigrateMediaGbifMediaIdIndex.sql`

4. Quality-History:
- Tabelle `quality_report_history`.
- Snapshot- und Compare-Endpunkte.
- umgesetzt in:
	- `Database/Backend/SQL/MigrateQualityReportHistory.sql`
	- `Database/Backend/SQL/RecordQualityReportSnapshot.sql`
	- `Database/Backend/App/repositories/core_repository.py`
	- `Database/Backend/App/controllers/core_controller.py`
	- `Database/Backend/App/routers/core_router.py`

5. DB-Validierung + Migrationen:
- CHECK-Constraints fuer zentrale Wertebereiche.
- versionierte Migrationen ueber `schema_migrations` + Runner.
- umgesetzt in:
	- `Database/Backend/SQL/MigrateDataValidationChecks.sql`
	- `Database/Backend/SQL/MigrateClimateValidationNormalization.sql`
	- `Database/Backend/SQL/MigrateSchemaMigrations.sql`
	- `Database/Backend/SQL/run_migrations.sh`

6. Konsistenz-Update (nach Sprint 6):
- Einheitliches `unknown` fuer Missing-Klassen (Ausnahme Hoehenlogik bewusst beibehalten).
- 404-Fehler fuer unbekannte Route jetzt im Standardformat `{"error", "message"}`.
- umgesetzt in:
	- `Database/Backend/App/core/classifications.py`
	- `Database/Backend/App/core/payloads.py`
	- `Database/Backend/App/core/main.py`

## Was jetzt noch gemacht werden soll

### Prioritaet A (naechster Sprint)
1. Data-Quality-Report erweitern:
- Duplikatindikatoren (z. B. gleiche Art + Ort + Datum).
- Invalid-Geo (Koordinaten ausserhalb Zielregion).
- Medien-Qualitaet (kaputte/leere URLs).
- Ziel: `/quality/report` um diese KPI-Bloecke ergaenzen.

2. Statistik-Endpunkte fuer Frontend-Charts einfuehren:
- Top-Familien
- Arten pro Land
- Beobachtungen pro Jahr
- Ziel: klarer Response-Vertrag fuer Diagramme statt Frontend-Selbstaggregation.

3. API-Vertrag und Implementierung final synchronisieren:
- `API-VERTRAG.md` auf reale Klassencodes/Beispiele anpassen (keine Altwerte).
- OpenAPI-Beispiele und Contract-Tests darauf abstimmen.

### Prioritaet B (kurz danach)
1. Automatische Quality-Snapshots im Betrieb:
- Snapshot nach erfolgreichem Import/Seed und optional per Cron/Job.

2. Migrationsrunner in CI integrieren:
- Pipeline-Check: Migrationen laufen auf leerer Test-DB fehlerfrei.

3. Performance-Runde 2:
- EXPLAIN-Baseline fuer neue Endpunkte (`/quality/report/history`, Media, Stats).

## Coole Erweiterungen (optional, aber sinnvoll)

1. GeoJSON Heatmap-Endpunkt:
- Dichtekarten pro Art/Familie und Zeitraum fuer Karten-Layer.

2. Aehnlichkeits-Endpunkt fuer Arten:
- "aehnliche Lebensraeume" auf Basis Klima/Boden/Vegetation-Bands.

3. Beobachtungs-Qualitaets-Score:
- Score aus Datumspraezision, Taxon-Aufloesung, Geo-Unsicherheit, Medienverfuegbarkeit.

4. Materialized Summary Tables:
- Vorgefertigte Aggregationen fuer Dashboards (schnellere Ladezeiten).

5. Delta-Alerting:
- Warnung, wenn sich Nullraten/EE-Coverage nach Import stark verschlechtern.

## Team-Standard (verbindlich)

1. Schema-Aenderungen nur ueber Migrationen.
2. Migrationen nur ueber Runner:
- `Database/Backend/SQL/run_migrations.sh`
3. Nach jeder relevanten Aenderung:
- `Database/Docs/API-VERTRAG.md` aktualisieren.
- Contract-Tests erweitern.
- `Database/Docs/WORKLOG.md` kurz nachziehen.