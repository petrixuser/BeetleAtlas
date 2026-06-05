# Backend Next Steps (Beetle Project)

## Zielbild
Das Backend soll nicht nur Tabellen ausliefern, sondern als Such- und Karten-API fuer das Frontend dienen:
- filtern nach Taxonomie, Zeit, Ort, Klima
- Punkte auf Suedamerika-Karte ausgeben
- Detailansicht pro Spot inkl. Klima, Bilder und Metadaten

## Was schon da ist
- Grund-API mit FastAPI
- DB-Verbindung zu MySQL
- Endpunkte fuer Health, Stats, Species, Observations, Climate per Location

## Was noch gebraucht wird (Must-Have)
1. API-Vertrag mit Frontend festziehen
- Einheitliche Query-Parameter (z. B. `from_date`, `to_date`, `bbox`, `family`, `genus`, `has_image`)
- Einheitliches Response-Format (`items`, `total`, `page`, `page_size`)
- Fehlerformat mit klaren Codes

2. Karten-Endpunkte bauen
- `GET /map/points` fuer Punktliste mit Filtern
- `GET /map/points/geojson` fuer direkte Kartenintegration
- `GET /location/{id}/detail` fuer Klick auf Marker

3. Such-Endpunkte erweitern
- Taxonomiefilter: family, genus, scientific_name
- Raumfilter: country, region, bbox
- Zeitfilter: year, from/to
- Klimafilter: ranges fuer temperature, precipitation, ndvi, soil_moisture

4. Pagination + Sorting konsequent
- `limit`, `offset` oder `page`, `page_size`
- sortierbare Felder sauber whitelisten

5. Performance absichern
- EXPLAIN fuer schwere Queries
- noetige Indexe nachziehen (vor allem auf Join-/Filterfeldern)
- bei Kartenabfragen Clustering/Bounding-Strategie einplanen

## Gute Erweiterungen (Nice-to-Have)
1. Spot Preview mit Satellitenbild
- Option A: Google Maps Static API (kostenpflichtig ab Nutzungsschwelle)
- Option B: Sentinel-2 Thumbnail ueber Earth Engine (fachlich stark)
- Option C: XYZ-Kartenlayer im Frontend (z. B. Esri/MapTiler)

2. Bild-Overlay fuer Fundorte
- Markercluster mit Bild-Icon bei `has_image=1`
- Klick zeigt Medienliste (`media.image_url`) + Rechtehinweise (`license`, `rights_holder`)

3. Klima-Zusammenfassungen
- `GET /climate/summary` pro Art, Region, Zeitraum
- Anomalien oder Trends (z. B. Temp-Mittel pro Jahr)

4. Export-Endpunkte
- `GET /export/observations.csv`
- `GET /export/map_points.geojson`

5. Qualitaetsmetriken
- `GET /quality/report`
- fehlende Klimawerte, fehlende Bilder, Datumsabdeckung

## Konkrete Endpoint-Vorschlaege
1. `GET /map/points`
Parameter:
- `bbox=minLon,minLat,maxLon,maxLat`
- `from_date`, `to_date`
- `family`, `genus`, `scientific_name`
- `has_image`
Rueckgabe:
- `location_id`, `lat`, `lon`, `observation_count`, optionale Klimaaggregate

2. `GET /map/points/geojson`
- gleiche Filter wie oben
- Rueckgabe als FeatureCollection

3. `GET /location/{location_id}/detail`
Rueckgabe:
- Standortdaten
- Top-Arten am Spot
- Zeitreihe aus `climate_snapshot`
- Medienvorschau

4. `GET /search/observations`
- kombinierte Filter, paginiert
- ideal fuer Tabellenansicht im Frontend

## DB- und Query-Hinweise
1. Sinnvolle Zusatzindexe pruefen
- `observation(beetle_id, location_id, event_date)`
- `climate_snapshot(location_id, snapshot_date)` (already unique)
- `location(country, region)`

2. Klima-Joins auf Monatslogik abstimmen
- `snapshot_date` ist Monatsanfang
- im Frontend klar kommunizieren: Klima auf Monats-/Jahresaggregat

## Sicherheit und Betrieb
1. `.env` nicht committen
2. CORS fuer Frontend-Host setzen
3. Basic Rate-Limit fuer oeffentliche Endpunkte
4. Logging fuer langsame Queries
5. OpenAPI-Doku aktuell halten

## Vorschlag fuer naechsten Sprint
1. API-Vertrag mit Frontend finalisieren (30-45 min)
2. `GET /map/points` und `GET /location/{id}/detail` implementieren
3. GeoJSON-Endpoint hinzufuegen
4. 1 Kartenansicht im Frontend anschliessen
5. Spot-Preview (Satellit oder Basemap-Layer) als Demo-Highlight

## Kurzfazit
Das Fundament steht. Der wichtigste naechste Schritt ist die gezielte Karten- und Such-API fuer den Frontend-Flow. Mit einem Spot-Detail inkl. Klima-Zeitreihe und optionalem Satelliten-Preview habt ihr eine sehr gute, vorzeigbare Demo.
