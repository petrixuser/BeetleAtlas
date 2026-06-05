# Worklog: Beetle Box

Dieser Worklog haelt den aktiven Arbeitsstand fest. Er soll nach jeder relevanten Aenderung
aktualisiert werden, damit die Arbeit bei einer neuen Session ohne Kontextverlust fortgesetzt
werden kann.

## Arbeitsregel

Bei jeder neuen Session zuerst lesen:

1. `Käferliebe/docs/PFLICHTENHEFT.md`
2. `Käferliebe/docs/WORKLOG.md`
3. Relevante Dateien in `Käferliebe/frontend/`

Nach jeder relevanten Aenderung aktualisieren:

- Was wurde gemacht?
- Welche Entscheidung wurde getroffen?
- Was ist offen?
- Was ist der naechste sinnvolle Schritt?

## Aktueller Stand

Datum: 2026-06-05

Projektname:

- Beetle Box (Frontend-Name) / BeetleAtlas (GitHub-Repo-Name)

Frontend-Pfad:

- `Käferliebe/frontend/`

Dokumentation:

- `Käferliebe/docs/PFLICHTENHEFT.md`
- `Käferliebe/docs/ENTWICKLUNGSPLAN.md`
- `Käferliebe/docs/WORKLOG.md`

Aktueller lokaler Server:

- `http://localhost:4175/`
- Starten: `cd frontend && python3 -m http.server 4175`

GitHub-Repository:

- https://github.com/petrixuser/BeetleAtlas

Live-URL (nach Portainer/NPM-Setup):

- https://kafer.server-work.de

Docker-Image:

- `ghcr.io/petrixuser/beetleatlas:latest`

## Bisher umgesetzt

Frontend-Grundgeruest:

- `Käferliebe/frontend/index.html`
- `Käferliebe/frontend/styles.css`
- `Käferliebe/frontend/app.js`
- `Käferliebe/frontend/README.md`

Funktionen:

- Header mit `Beetle Box`
- Suchfeld fuer Arten
- Filter fuer Klimazone, Vegetation und Hoehenlage
- Ergebnisliste mit Demo-Kaeferdaten
- Detailbereich fuer ausgewaehlte Kaeferart
- Atlas-Grundkarte von Lateinamerika
- SVG-Karte mit Zoom, Pan und Reset
- Echte Laendergrenzen aus GeoJSON-Daten
- Laendernamen als klickbare Elemente
- Rechte Sidebar fuer Laenderinformationen
- Kaeferpunkte als klickbare Punkte
- Kleines Popup fuer Punktinformationen

Kartendaten:

- `Käferliebe/frontend/assets/latin-america-countries.geojson`
- `Käferliebe/frontend/assets/latin-america-countries.js`

Warum beide Dateien existieren:

- `.geojson` ist die eigentliche Kartendatenquelle.
- `.js` enthaelt dieselben Daten als globale Variable, damit Chrome die Karte robuster laden kann
  und nicht an `fetch()`/Dateizugriff scheitert.

## Wichtige Entscheidungen

- Das Frontend greift nicht direkt auf die Datenbank zu.
- Spaetere Daten kommen ueber Backend/API.
- Die bisherige SVG-/GeoJSON-Karte ist nur ein Zwischenstand.
- Zielarchitektur ist kuenftig eine Google-Maps-basierte Karte.
- Es duerfen nur kostenkontrollierte Google-Maps-Funktionen innerhalb kostenloser Kontingente
  bzw. aktuell kostenfreier Preview-Funktionen genutzt werden.
- Der bereitgestellte Entwicklungs-API-Key darf nicht fest in versionierte Dateien geschrieben
  werden.
- Farben fuer Hoehe, Klima und Vegetation sind bis zur Google-Maps-Zielplanung zurueckgestellt.
- Laenderinformationen sind aktuell Platzhalter.
- Punktinformationen sind aktuell Platzhalter.
- Aesthetik und Uebersichtlichkeit haben Prioritaet vor maximaler Detailtiefe.

## Bekannte Einschraenkungen

- Die Karte enthaelt echte Laendergrenzen, aber Labelpositionen sind manuell gesetzt.
- Kleine Laender in Zentralamerika und der Karibik koennen bei niedriger Zoomstufe eng wirken.
- Die Kaeferdaten sind Demo-Daten.
- Die Sidebar ist noch nicht mit echten Laenderinformationen befuellt.
- Das Punkt-Popup ist noch nicht mit echten Fundinformationen befuellt.
- Es gibt noch keine echte Backend-Anbindung.

## Naechste sinnvolle Schritte

1. Google-Maps-Sicherheitscheck aus `Käferliebe/docs/ENTWICKLUNGSPLAN.md` starten.
2. API-Key-Strategie festlegen: lokale Konfiguration, keine Commit-Speicherung.
3. Google-Cloud-Sicherheitscheck durchfuehren: API Restrictions, HTTP Referrer, Quotas, Budgetwarnungen.
4. Danach 2D Google Maps als ersten Karten-Meilenstein einbauen.
5. Backend-API-Vertrag fuer Kaeferfundorte und Filter abstimmen.
6. Danach Marker/Popups/Filter auf Google Maps anbinden.
7. 3D und Themenebenen erst nach erneuter Kosten- und SKU-Pruefung planen.

## Session-Ende (2026-06-05) — Aktueller Stand

### Was in dieser Session gemacht wurde

Phase 0 bis Phase 3 vollstaendig abgeschlossen.
Phase 4 (Themenebenen) vollstaendig neu implementiert — echte Geodaten statt statischer Bilder.
CI/CD-Pipeline eingerichtet, getestet und vollstaendig funktionsfaehig.

### Aktueller lokaler Server

```
cd "/Users/perrystaedtke/Documents/New project/Käferliebe/frontend"
python3 -m http.server 4175
```

Dann http://localhost:4175 im Browser oeffnen.

### Funktioniert jetzt

- Google Maps 2D als Hauptkarte (ersetzt die alte SVG-Karte)
- Lateinamerika zentriert beim Start (center -15/-60, zoom 4)
- Laendergrenzen als klickbarer GeoJSON-Layer (google.maps.Data)
  — Klick auf Land oeffnet die rechte Sidebar
  — Hover-Effekt auf Laendern
- Kaeferfundorte als rote Marker auf der Karte
  — Klick oeffnet ein InfoWindow mit Art, Familie, Fundort, Hoehe, Klima, Vegetation
  — InfoWindow bleibt synchron bei Zoom und Pan
- Filter (Suche, Klima, Vegetation, Hoehe) aktualisieren Marker und Ergebnisliste
- Interaktions-Koordination: Marker schliesst Sidebar, Land-Klick schliesst InfoWindow
- Ansichts-Toggle ueber der Karte: Normal / Hoehe / Klima / Vegetation
  — Hoehe: OpenTopoMap-Kacheln via ImageMapType (zoom-adaptiv, weltweit korrekt)
  — Klima: Echte Koeppen-Geiger-Polygone via google.maps.Data (Beck et al. 2023, 1991-2020)
  — Vegetation: Echte WWF Ecoregion-Polygone via google.maps.Data (14 Biome)
- Datenservice loadBeetles(): Demo-Modus oder Backend-Modus (via API_BASE_URL in config.local.js)
- SVG-Karte bleibt als ausgeblendeter Fallback im DOM erhalten

### Dateistruktur nach dieser Session

```
Kaeferliebe/
  frontend/
    index.html          — Hauptseite
    styles.css          — Layout und Styling
    app.js              — Gesamte Anwendungslogik
    config.local.js     — API-Key (NICHT committen, in .gitignore)
    config.example.js   — Vorlage fuer neuen Entwickler
    data/
      demo-beetles.js   — Demo-Kaeferdaten (window.DEMO_BEETLES)
    assets/
      koppen-latam.geojson     — Koeppen-Geiger Klimazonen (Beck et al. 2023, 1.6 MB)
      ecoregions-latam.geojson — WWF Terrestrial Ecoregions (2.9 MB)
      latin-america-countries.geojson
      latin-america-countries.js
      map-elevation.png        — veraltet, nicht mehr genutzt
      map-climate.jpg          — veraltet, nicht mehr genutzt
      map-vegetation.png       — veraltet, nicht mehr genutzt
    vendor/leaflet/     — nicht mehr aktiv genutzt, kann spaeter entfernt werden
  docs/
    PFLICHTENHEFT.md    — Single Source of Truth fuer Anforderungen
    ENTWICKLUNGSPLAN.md — Phasen, Module, Arbeitspakete
    WORKLOG.md          — dieser Worklog
    API-VERTRAG.md      — Endpunkte und JSON-Felder fuer Backend
    README.md
  .gitignore
  README.md
```

### Noch offen / naechste Schritte

1. Google Cloud Sicherheitscheck (manuell im Google Cloud Console):
   - API-Key HTTP-Referrer auf `localhost:4175/*` und `kafer.server-work.de/*` einschraenken.
   - API-Key auf Maps JavaScript API beschraenken.
   - Budget-Alert setzen (z. B. 5 USD).

2. Workflow Node.js-24-Migration: In `.github/workflows/build-and-deploy.yml` die Zeile
   `FORCE_JAVASCRIPT_ACTIONS_TO_NODE24: true` unter `env:` ergaenzen (Pflicht ab Sept. 2026).

3. Backend-Anbindung: wenn Backend laeuft, `API_BASE_URL` als Portainer-Umgebungsvariable
   eintragen — der Entrypoint schreibt sie automatisch in config.local.js.

4. Phase 5 (Performance): Bounding-Box-basiertes Nachladen, Clustering fuer grosse Datenmengen.

5. Phase 6 (3D): erst nach SKU/Kosten-Pruefung.

6. Ameisenstrasse: ganz am Ende, nach stabilem Layout.

7. Aufraeumsachen (niedrige Prioritaet):
   - map-elevation.png, map-climate.jpg, map-vegetation.png (veraltet, aus Docker ausgeschlossen)
   - frontend/vendor/leaflet/ (nicht mehr genutzt, aus Docker ausgeschlossen)

### Bekannte Einschraenkungen

- Sidebar zeigt noch Platzhaltertext — spaeter mit echten Laenderdaten befuellen.
- Laendernamen auf Google Maps kommen von Google selbst (Englisch je nach Spracheinstellung).
- Koeppen- und Vegetation-Layer werden beim ersten Klick geladen (~1-2s), danach gecacht.
- GMAPS_KEY muss in Portainer als Umgebungsvariable gesetzt sein, sonst laedt die Karte nicht.

---

## CI/CD & Deployment — Abgeschlossen (2026-06-05)

### GitHub Repository, Docker, GitHub Actions, Portainer

Neue Dateien im Repo:

- `Dockerfile`: nginx:alpine, kein Build-Schritt (statische App).
  Kopiert `frontend/` nach `/usr/share/nginx/html/`.
  Startet ueber `docker-entrypoint.sh`.
- `docker-entrypoint.sh`: Schreibt `config.local.js` zur Laufzeit aus Umgebungsvariablen.
  Injiziert `GMAPS_KEY` und `API_BASE_URL` — keine Secrets im Image.
- `docker-compose.yml`: Portainer-Stack-Vorlage.
  Image: `ghcr.io/petrixuser/beetleatlas:latest`.
  Netzwerk: `npm_proxy` (extern, geteilt mit Nginx Proxy Manager).
  Kein Host-Port-Mapping.
- `.dockerignore`: Schliessst `.git`, `docs/`, `vendor/`, alte Karten-PNGs aus dem Image aus.
- `.github/workflows/build-and-deploy.yml`: Vollstaendige CI/CD-Pipeline.
  Trigger: Push auf `main` oder `workflow_dispatch`.
  Jobs: `build` (Docker-Image bauen + nach GHCR pushen) → `deploy` (Portainer Webhook aufrufen).
  GHCR-Auth: `secrets.GITHUB_TOKEN` (automatisch, kein manuelles Secret noetig).
  Portainer-Webhook: `secrets.PORTAINER_WEBHOOK_URL` (manuell als GitHub Secret gesetzt).
- `README.md`: Vollstaendige Deployment-Dokumentation (Architektur, Portainer-Setup,
  NPM-Konfiguration, Rollback-Anleitung, Datensatz-Quellen).
- `.gitignore`: Ergaenzt um `.claude/`, `node_modules/`, `.env.*`.

Wichtige Entscheidungen:

- Kein SSH-Deployment. NAS baut nicht selbst — zieht nur fertiges Image aus GHCR.
- `GMAPS_KEY` wird niemals in das Image gebacken, sondern per Entrypoint injiziert.
- Portainer-Webhook-Step laueft durch (skipped) wenn Secret nicht gesetzt — kein Pipeline-Fehler.
- Image-Name lowercase `beetleatlas` (GHCR-Anforderung), Repository-Name `BeetleAtlas`.

Testergebnis (workflow_dispatch, Run 27017661063):

- Build and push image: ✅ 17s
- GHCR Image: ✅ `ghcr.io/petrixuser/beetleatlas:latest` + `sha-06f67a8`
- Portainer webhook: ✅ HTTP 2xx, "Portainer webhook triggered."
- Deploy job: ✅ 5s

GitHub Secret gesetzt:

- `PORTAINER_WEBHOOK_URL`: gesetzt (Wert vertraulich).

Offene manuelle Schritte nach diesem Schritt — alle erledigt:

- [x] GitHub Repo BeetleAtlas angelegt (public)
- [x] Portainer Stack BeetleAtlas erstellt
- [x] `GMAPS_KEY` in Portainer Stack-Umgebung eingetragen
- [x] Portainer Webhook aktiviert und URL als GitHub Secret gesetzt
- [x] Nginx Proxy Manager: kafer.server-work.de → BeetleAtlas:80

---

## Phase 4 (Themenebenen) — Abgeschlossen (2026-06-05)

### Echte Geodaten-Layer fuer Hoehe, Klima, Vegetation

Geaenderte Dateien:

- `frontend/app.js`:
  - `LATAM_BOUNDS`, `OVERLAY_SOURCES`, `LEGEND_DATA`, `activeOverlay` entfernt.
  - `setMapView()` komplett neu geschrieben (async).
  - Hoehe: `google.maps.ImageMapType` mit OpenTopoMap-Kacheln
    (URL: `https://tile.opentopomap.org/{z}/{x}/{y}.png`, opacity 0.85).
    Kacheln laden dynamisch, zoomen korrekt, weltweit gueltig.
    Ausgeloester SKU: keiner (Kacheln kommen von OpenTopoMap, nicht Google).
  - Klima: separates `google.maps.Data`-Objekt, laedt `assets/koppen-latam.geojson`
    per fetch() beim ersten Aufruf, wird danach gecacht.
    Style: fillColor aus GeoJSON-Property `color`, fillOpacity 0.72, strokeWeight 0.
  - Vegetation: separates `google.maps.Data`-Objekt, laedt `assets/ecoregions-latam.geojson`
    per fetch() beim ersten Aufruf, wird danach gecacht.
    Style: analog zu Klima.
  - `hideAllThemeLayers()` als zentrale Hilfsfunktion.
- `frontend/index.html`:
  - Hoehenlegende aktualisiert (OpenTopoMap-Farbschema, Quellenangabe).
  - Neue Klimazonen-Legende mit Koeppen-Gruppen A/B/C/D/E und Quellenangabe.
  - Neue Vegetations-Legende mit 14 WWF-Biomen und Quellenangabe.
- `frontend/styles.css`:
  - `.map-legend`: max-height 420px, overflow-y auto (fuer lange Klimalegende).
  - `.legend-group`, `.legend-group-title` neu fuer gruppierte Legenden.

Neue Daten-Assets (einmalig aus Quelldaten erzeugt):

- `frontend/assets/koppen-latam.geojson` (1.6 MB):
  Koeppen-Geiger Klassifikation 1991-2020, 0.1-Grad-Aufloesung, auf Lateinamerika geclippt,
  Polygone mit tolerance=0.06 vereinfacht. Quelle: Beck et al. (2023), CC-BY 4.0.
  Verarbeitung: rasterio (Python) aus GeoTIFF -> polygonize -> GeoJSON.

- `frontend/assets/ecoregions-latam.geojson` (2.9 MB):
  WWF Terrestrial Ecoregions of the World (Olson et al. 2001), 14 Biome,
  auf Lateinamerika geclippt (NT+NA Realm), Polygone mit tolerance=0.05 vereinfacht.
  Quelle: WWF (freie Nutzung fuer nicht-kommerzielle Projekte).
  Verarbeitung: fiona + shapely (Python) aus Shapefile -> GeoJSON.

Wichtige Entscheidungen:

- GroundOverlay (altes Verfahren mit statischen Bildern) vollstaendig entfernt.
- Fuer Hoehe kein eigenes GeoJSON-Layer notwendig: OpenTopoMap-Kacheln sind
  ausreichend praezise und visuell hochwertig.
- Koeppen und Vegetation: separate google.maps.Data-Instanzen statt googleMapInstance.data,
  damit Laendergrenzen-Layer unveraendert bleibt.
- Lazy Loading: Layer werden erst bei erstem Klick geladen (nicht beim Seitenstart).

---

## Phase 3 — Abgeschlossen (2026-06-05)

### Datenservice und Backend-Vorbereitung

Geaenderte und neue Dateien:

- `frontend/data/demo-beetles.js` (neu): Demo-Daten als `window.DEMO_BEETLES`, ausgelagert
  aus `app.js`. Bleibt aktiv im Mock-Modus.
- `frontend/index.html`: Script-Tag fuer `data/demo-beetles.js` eingefuegt.
- `frontend/app.js`:
  - `beetles`-Array durch `let beetles = []` ersetzt.
  - `loadBeetles()` async Funktion eingefuehrt: laedt echte Daten wenn `window.API_BASE_URL`
    gesetzt, sonst `window.DEMO_BEETLES`.
  - Initialisierung auf `await loadBeetles()` umgestellt (IIFE).
  - Fehlerfall in `loadBeetles()` faellt auf Demo-Daten zurueck.
- `docs/API-VERTRAG.md` (neu): Endpunkte, JSON-Felder, Filterparameter und Performance-Regeln
  fuer Backend-Anbindung dokumentiert.

Backend-Anbindung aktivieren:
In `frontend/config.local.js` `window.API_BASE_URL = "http://localhost:8080"` setzen.
Ohne diesen Wert laueft das Frontend weiterhin im Demo-Modus.

---

## Phase 2 — Abgeschlossen (2026-06-05)

### GeoJSON-Overlay und Interaktions-Koordination

Geaenderte Dateien:

- `frontend/app.js`:
  - `initGeoJsonLayer()`: Laedt `window.LATIN_AMERICA_COUNTRIES` als `google.maps.Data` Layer.
    Zeichnet Laendergrenzen auf der Google Maps Karte.
    Hover-Effekt: Laender heben sich hervor.
    Klick auf Land: schliesst InfoWindow, oeffnet Sidebar mit Laendername.
  - Marker-Klick schliesst Sidebar (`closeCountrySidebar()` vor `InfoWindow.open()`).
  - `initGeoJsonLayer()` wird in `window.initMap()` nach Karten-Initialisierung aufgerufen.

Laender-Klick ist damit wieder verfuegbar — wie in der SVG-Version.
Ausgeloeste SKU: weiterhin nur `Dynamic Maps` (google.maps.Data ist Teil der Maps JS API,
keine Zusatz-SKU).

---

## Phase 1 — Abgeschlossen (2026-06-05)

### Google Maps 2D Grundkarte eingebaut

Geaenderte Dateien:

- `frontend/index.html`:
  - SVG in `<div id="svgFallback" style="display:none">` gewrapped (Fallback, nicht geloescht)
  - Neuer `<div id="googleMap">` Container angelegt
  - Lade-Overlay `#mapLoadingState` und Fehler-Overlay `#mapErrorState` eingefuegt
  - `config.local.js` als erstes Script eingebunden
- `frontend/styles.css`:
  - `#googleMap` mit `height: 600px` und `width: 100%` gestylt (kritisch fuer Google Maps)
  - `.map-state-overlay` fuer Lade- und Fehlerzustand
- `frontend/app.js`:
  - `loadGoogleMapsScript()` laedt Google Maps Script dynamisch (Key nicht im HTML)
  - `window.initMap()` initialisiert die Karte auf Lateinamerika (center -15/-60, zoom 4)
  - `window.gm_authFailure` zeigt Fehler-Overlay bei ungueltigem Key
  - `renderGoogleMapMarkers()` rendert Kaeferpunkte als Google Maps Marker
  - `activeInfoWindow` (google.maps.InfoWindow) ersetzt das SVG-Popup (bleibt synchron mit Karte)
  - `renderMapPoints()` als gemeinsamer Einstiegspunkt: Google Maps oder SVG-Fallback
  - Filter-Render (`render()`) aktualisiert automatisch Google Maps Marker

Ausgeloeste SKU: `Dynamic Maps` (Maps JavaScript API Kartenladung)

SVG-Fallback: Bleibt im DOM unter `#svgFallback`, ausgeblendet. Wird spaeter entfernt, sobald Google Maps stabil laeuft.

Naechster Schritt: Phase 2 — Sidebar-Interaktion ueberarbeiten, Filter und Detailansicht weiter optimieren, dann Backend-Vorbereitung.

---

## Phase 0 — Abgeschlossen (2026-06-05)

### Key-Strategie

Umgesetzt:

- `frontend/config.local.js` — enthaelt den echten Google Maps API-Key (`window.GMAPS_KEY`).
  Darf niemals ins Repository. Steht in `.gitignore`.
- `frontend/config.example.js` — Vorlage ohne echten Key. Wird committet.
  Neue Entwickler kopieren diese Datei als `config.local.js` und tragen ihren Key ein.
- `.gitignore` im Projektroot angelegt. Schliessst `frontend/config.local.js` aus.

### Google Cloud — ausstehende manuelle Schritte

Diese Schritte muessen manuell im Google Cloud Console erledigt werden:

1. API-Key einschraenken:
   - Application Restrictions → HTTP Referrers → `localhost:*`, `localhost:4173/*`
   - API Restrictions → "Restrict key" → nur "Maps JavaScript API"
2. Budget Alert setzen: Billing → Budgets & Alerts → z. B. 5 USD Warnschwelle
3. Sicherstellen, dass keine anderen APIs aktiviert sind (Places, Routes, Geocoding etc.)

Diese Schritte wurden noch nicht verifiziert. Vor Phase 1 pruefen.

### Naechster Schritt

Phase 1 starten: Google Maps 2D Grundkarte einbauen.
Abhaengigkeit: Google Cloud Sicherheitscheck (s. o.) sollte vorher erledigt sein.

---

## Letzte Aenderung

2026-06-05 — Phase 0:

- Pflichtenheft angelegt.
- Worklog angelegt.
- Aktueller Projektstand dokumentiert.
- Arbeitsregel festgelegt: Erst Pflichtenheft/Worklog aktualisieren, dann groessere Code-Aenderungen.

2026-06-05:

- Neue Anforderungen in das Pflichtenheft aufgenommen.
- Zielarchitektur auf Google Maps API umgestellt.
- Kostenregel dokumentiert: keine unkontrollierte Nutzung kostenpflichtiger APIs/SKUs.
- API-Key-Regel dokumentiert: Entwicklungskey nicht in versionierte Dateien schreiben.
- Zielansichten dokumentiert: 2D Standardkarte, 3D Karte, Hoehe, Klima, Vegetation.
- Backend-Kartenanbindung dokumentiert.
- Reaktive Popup-/Overlay-Anforderung dokumentiert.
- Ameisenstrasse als spaeteres UI-Feature dokumentiert.
- Offene Entscheidungen fuer Entwicklungsplan aktualisiert.

2026-06-05:

- Ausfuehrlicher Entwicklungsplan angelegt: `Käferliebe/docs/ENTWICKLUNGSPLAN.md`.
- Module, Phasen, Arbeitspakete, Abhaengigkeiten, Risiken und Abnahmekriterien dokumentiert.
- Naechste Schritte im Worklog auf Google-Maps-Sicherheitscheck und lokale Key-Strategie
  fokussiert.

2026-06-05:

- Alle Beetle-Box-/Kaeferprojekt-Dateien in den neuen Unterordner `Käferliebe/` verschoben.
- Dokumentation liegt jetzt unter `Käferliebe/docs/`.
- Frontend liegt jetzt unter `Käferliebe/frontend/`.
- Rover-/CE-Projektdateien bleiben im Repository-Root und sind dadurch sauber getrennt.
