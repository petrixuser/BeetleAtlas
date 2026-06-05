# API-Vertrag: Beetle Box

Dieses Dokument beschreibt die geplanten HTTP-Endpunkte zwischen Frontend und Backend.
Es dient als verbindliche Grundlage fuer die spaetere Backend-Implementierung.

Abgeleitet aus: `PFLICHTENHEFT.md`, Abschnitte 11, 12, 15.5

## Grundsatz

- Das Frontend kommuniziert ausschliesslich ueber HTTP mit dem Backend.
- Kein direkter Datenbankzugriff aus dem Frontend.
- Das Backend liefert JSON.
- Die Backend-URL wird in `frontend/config.local.js` als `window.API_BASE_URL` gesetzt.
- Ist `window.API_BASE_URL` nicht gesetzt, laedt das Frontend Demo-Daten aus
  `frontend/data/demo-beetles.js`.

## Endpunkte

### GET /api/beetles

Gibt eine gefilterte Liste von Kaeferarten zurueck.

**Query-Parameter:**

| Parameter   | Typ    | Beschreibung                                         |
|-------------|--------|------------------------------------------------------|
| `q`         | string | Freitext-Suche (Name, Familie, Fundort)              |
| `climate`   | string | Klimazone (z. B. `Tropisch`, `Gebirge`)              |
| `vegetation`| string | Vegetationszone (z. B. `Regenwald`, `Savanne`)       |
| `elevation` | string | Hoehengruppe: `low`, `mid`, `high`, `veryHigh`       |
| `limit`     | int    | Max. Anzahl Ergebnisse (Standard: 100)               |
| `offset`    | int    | Pagination-Offset (Standard: 0)                      |
| `temperature_band` | string | Temperaturband (`kalt`, `kuehl`, `warm`, `heiss`) |
| `precipitation_band` | string | Niederschlagsband (`sehr_trocken`, `trocken`, `feucht`, `sehr_feucht`) |
| `soil_moisture_band` | string | Bodenfeuchteband (`sehr_trocken`, `trocken`, `mittel`, `feucht`) |
| `ndvi_band` | string | Vegetationsdichteband (`geringe_vegetation`, `offene_vegetation`, `dichte_vegetation`, `sehr_dichte_vegetation`) |
| `humidity_band` | string | Luftfeuchteband (`trocken`, `moderat`, `feucht`, `sehr_feucht`) |
| `pressure_band` | string | Druck/Hoehenband (`hochgebirge`, `gebirge`, `hochland`, `tiefland`) |
| `light_pollution_band` | string | Nachtlichtklasse (`naturnah`, `laendlich`, `periurban`, `urban`) |
| `slope_band` | string | Reliefklasse (`flach`, `leicht_geneigt`, `huegelig`, `steil`) |
| `water_distance_band` | string | Gewaessernaehe (`ufernah`, `wassernah`, `inland`, `weit_von_wasser`) |
| `human_impact_band` | string | Anthropogener Einfluss (`minimal`, `niedrig`, `mittel`, `hoch`) |

**Beispiel-Antwort:**

```json
[
  {
    "id": "occ-001",
    "name": "Dynastes hercules",
    "family": "Scarabaeidae",
    "location": "Amazonas, Ecuador",
    "coordinates": [-78.2, -1.4],
    "climate": "Tropisch",
    "vegetation": "Regenwald",
    "elevation": 450,
    "temperature": 27,
    "soil": "Lehmiger Waldboden",
    "ee": {
      "raw": {
        "precipitation": 1860.2,
        "soilMoisture": 0.31,
        "ndvi": 0.72,
        "relativeHumidity": 82.1,
        "surfacePressureHpa": 965.4,
        "nighttimeLights": 1.2,
        "slope": 8.5,
        "distanceToWaterM": 430,
        "humanModification": 0.12,
        "landcoverClass": 20,
        "ecoregionId": 123,
        "biomeId": 2
      },
      "bands": {
        "temperature": "heiss",
        "precipitation": "feucht",
        "soilMoisture": "mittel",
        "ndvi": "sehr_dichte_vegetation",
        "humidity": "sehr_feucht",
        "pressure": "tiefland",
        "lightPollution": "naturnah",
        "slope": "leicht_geneigt",
        "waterDistance": "wassernah",
        "humanImpact": "niedrig"
      }
    }
  }
]
```

### Mapping-Logik fuer Earth-Engine-Daten

Diese Einordnungen werden serverseitig erzeugt, damit Frontend und Analyse-Endpunkte
einheitliche Kategorien verwenden koennen.

| Kategorie | Grundlage | Klassen |
|-----------|-----------|---------|
| `climate` | Temperatur, Niederschlag, Hoehe | `Tropisch`, `Subtropisch`, `Trocken`, `Gebirge`, `Gemaessigt` |
| `vegetation` | NDVI, `biome_id`, `landcover_class`, Hoehe | `Regenwald`, `Savanne`, `Trockenwald`, `Gebirgsvegetation`, `Grasland`, `Mangroven` |
| `soil` | `soil_ph`, `soil_organic_carbon` | `Saurer Boden`, `Humusreicher Boden`, `Alkalischer Boden`, `Lehmiger Waldboden` |
| `temperature_band` | `avg_temperature` (Fallback `worldclim_bio01`) | `kalt`, `kuehl`, `warm`, `heiss` |
| `precipitation_band` | `precipitation` (Fallback `worldclim_bio12`) | `sehr_trocken`, `trocken`, `feucht`, `sehr_feucht` |
| `soil_moisture_band` | `soil_moisture` | `sehr_trocken`, `trocken`, `mittel`, `feucht` |
| `ndvi_band` | `ndvi` | `geringe_vegetation`, `offene_vegetation`, `dichte_vegetation`, `sehr_dichte_vegetation` |
| `humidity_band` | `relative_humidity` | `trocken`, `moderat`, `feucht`, `sehr_feucht` |
| `pressure_band` | `surface_pressure_hpa` | `hochgebirge`, `gebirge`, `hochland`, `tiefland` |
| `light_pollution_band` | `nighttime_lights` | `naturnah`, `laendlich`, `periurban`, `urban` |
| `slope_band` | `slope` | `flach`, `leicht_geneigt`, `huegelig`, `steil` |
| `water_distance_band` | `distance_to_water_m` | `ufernah`, `wassernah`, `inland`, `weit_von_wasser` |
| `human_impact_band` | `human_modification` | `minimal`, `niedrig`, `mittel`, `hoch` |

---

### GET /api/beetles/:id

Gibt einen einzelnen Kaefereintrag zurueck.

**Beispiel-Antwort:**

```json
{
  "id": "occ-001",
  "name": "Dynastes hercules",
  "family": "Scarabaeidae",
  "location": "Amazonas, Ecuador",
  "coordinates": [-78.2, -1.4],
  "climate": "Tropisch",
  "vegetation": "Regenwald",
  "elevation": 450,
  "temperature": 27,
  "soil": "Lehmiger Waldboden",
  "observedAt": "2024-05-12"
}
```

---

### GET /api/map/points

Gibt aggregierte oder gefilterte Kartenpunkte zurueck.
Dieser Endpunkt ist performance-kritisch und muss Backend-seitig filtern.

**Query-Parameter:**

| Parameter   | Typ    | Beschreibung                                          |
|-------------|--------|-------------------------------------------------------|
| `bbox`      | string | Bounding Box: `minLng,minLat,maxLng,maxLat`           |
| `zoom`      | int    | Aktuelle Zoomstufe (fuer Aggregation)                 |
| `climate`   | string | Filter Klimazone                                      |
| `vegetation`| string | Filter Vegetation                                     |
| `elevation` | string | Filter Hoehengruppe                                   |
| `q`         | string | Freitext-Suche                                        |
| `limit`     | int    | Max. Punkte (Standard: 500)                           |

**Beispiel-Antwort:**

```json
[
  {
    "id": "occ-001",
    "speciesName": "Dynastes hercules",
    "lat": -1.4,
    "lng": -78.2,
    "elevation": 450,
    "climate": "Tropisch",
    "vegetation": "Regenwald",
    "observedAt": "2024-05-12"
  }
]
```

Bei niedrigem Zoom soll das Backend aggregierte Cluster-Punkte liefern:

```json
[
  {
    "lat": -5.0,
    "lng": -75.0,
    "count": 1423,
    "isCluster": true
  }
]
```

---

### GET /api/filters

Gibt verfuegbare Filterwerte zurueck (z. B. fuer dynamische Dropdowns).

**Beispiel-Antwort:**

```json
{
  "climates": ["Tropisch", "Subtropisch", "Trocken", "Gebirge", "Gemaessigt"],
  "vegetations": ["Regenwald", "Savanne", "Trockenwald", "Gebirgsvegetation", "Grasland", "Mangroven"],
  "elevations": ["low", "mid", "high", "veryHigh"]
}
```

---

### GET /api/field-mappings

Liefert die serverseitig definierten Kategorien fuer alle Felder in
`beetle_species`, `location`, `observation`, `media` und `climate_snapshot`.

Damit koennen Frontend und Analyse-Tools dieselben Klassengrenzen verwenden,
auch fuer Felder, die im Frontend aktuell noch nicht angezeigt werden.

---

### GET /api/countries/:countryCode

Gibt Informationen zu einem Land zurueck (fuer die Sidebar).

**Beispiel-Antwort:**

```json
{
  "code": "EC",
  "name": "Ecuador",
  "speciesCount": 312,
  "topClimates": ["Tropisch", "Gebirge"],
  "topVegetations": ["Regenwald", "Gebirgsvegetation"],
  "elevationRange": [0, 6268]
}
```

---

## Feldnamen-Vereinbarung

Alle Felder werden in `camelCase` geliefert.
Frontend und Backend verwenden exakt dieselben Feldnamen (keine Umbenennungen im Frontend).

| Feld          | Typ      | Beschreibung                                |
|---------------|----------|---------------------------------------------|
| `id`          | string   | Eindeutige ID des Fundorts                  |
| `name`        | string   | Artname (lateinisch)                        |
| `family`      | string   | Familie                                     |
| `location`    | string   | Beschreibender Fundortname                  |
| `coordinates` | [lng,lat]| GeoJSON-Konvention: Laengengrad zuerst      |
| `lat`         | float    | Breitengrad (alternative zu coordinates)    |
| `lng`         | float    | Laengengrad (alternative zu coordinates)    |
| `climate`     | string   | Klimazone (deutsch)                         |
| `vegetation`  | string   | Vegetationszone (deutsch)                   |
| `elevation`   | int      | Hoehe in Metern ueber NN                    |
| `temperature` | float    | Temperatur in Grad Celsius                  |
| `soil`        | string   | Bodentyp                                    |
| `observedAt`  | string   | Beobachtungsdatum (ISO 8601: YYYY-MM-DD)    |

## Fehlerformat

```json
{
  "error": "not_found",
  "message": "Kein Eintrag mit dieser ID gefunden."
}
```

HTTP-Statuscodes: `200 OK`, `400 Bad Request`, `404 Not Found`, `500 Internal Server Error`

## Performance-Regeln

- `GET /api/map/points` darf nicht alle Rohpunkte zurueckgeben.
- Bei mehr als 2 Mio. Datensaetzen ist Bounding-Box-Filter Pflicht.
- Aggregation/Clustering wird ab Zoomstufe < 7 empfohlen.
- Maximale Antwortgroesse: 500 Punkte pro Request.
- Das Frontend setzt Debounce von 300ms vor jedem neuen Request.
