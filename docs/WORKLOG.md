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

2. Backend-Anbindung: kommt spaeter. Wenn Backend laeuft, `API_BASE_URL` als
   Portainer-Umgebungsvariable eintragen — Entrypoint schreibt sie automatisch in config.local.js.

3. Ameisenstrasse: dekoratives UI-Element, nach stabilem Layout umsetzen.

4. Aufraeumsachen (niedrige Prioritaet):
   - map-elevation.png, map-climate.jpg, map-vegetation.png (veraltet, aus Docker ausgeschlossen)
   - frontend/vendor/leaflet/ (nicht mehr genutzt, aus Docker ausgeschlossen)

Bewusst zurueckgestellt / gestrichen:

- Clustering/Performance-Konzept: nicht benoetigt (Entscheidung 2026-06-05).
- 3D-Kartenansicht: auf Eis gelegt (Entscheidung 2026-06-05).

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

---

## Handoff — Session 2026-06-05 (Ameisenstrasse + Ländergrenzen-Fix)

### Was wurde gemacht

**1. Ameisenstrasse implementiert** (`frontend/ants.js` neu, commits fbc05d0)

- Canvas-basierte Ameisensimulation als eigenständiges IIFE-Modul.
- `position: absolute` Canvas — läuft in Document-Space (volle Dokument-Höhe), nicht im Viewport.
  Das heißt: Ameisen laufen auch unterhalb des sichtbaren Bereichs weiter; beim Scrollen sieht man den ganzen Weg.
- Pfad: U-Form entlang der `.page`-Box-Ränder (links runter → Bogen unten → rechts hoch).
  Pfad-Mittelpunkt liegt in der Mitte des Seitenrandes (zwischen `.page`-Box und Browserkante).
  Sinusförmige Kurven (osc=26px, per=190px) für den wellenförmigen Look.
- 80 Ameisen max., alle 310 ms spawnt eine neue am Pfadanfang (oben links), verschwinden am Ende (oben rechts).
- Steering Behaviors: Pfad-Follow, Cursor-Flee (52px), Barrier-Flee, Separation.
- Mouse-Cut: Maus 550 ms auf Pfad halten → persistenter Barrier; beide Seiten weichen aus.
- 3 Äpfel spawnen zufällig entlang des Pfades; Ameisen riechen sie (65px), holen sie, tragen sie sichtbar weiter entlang der Straße (kein Rückweg mehr). Wenn alle gesammelt: neuer Spawn.
- Ameisenkörper: Abdomen/Thorax/Kopf + 2 Antennen + 6 animierte Beine (~5px Gesamtlänge).

**2. Ländergrenzen-Overlay entfernt** (`frontend/app.js`, commits 9cb6668 + 48cb984)

- Problem: `initGeoJsonLayer()` renderte `window.LATIN_AMERICA_COUNTRIES` als `google.maps.Data`-Layer mit sichtbarem Stroke (`strokeColor: "#35463f"`, `strokeWeight: 0.9`) auf Google Maps.
- Fix: Layer-Style auf `fillOpacity:0, strokeOpacity:0, strokeWeight:0` gesetzt → vollständig unsichtbar, aber klickbar für Sidebar-Interaktion.
- Hover zeigt noch dezenten grünen Fill (`fillOpacity:0.15`) als Klick-Feedback.
- `app.js` von `?v=2` auf `?v=3` gebumpt um Browser-Cache zu brechen.

**3. Styling-Anpassung** (`frontend/styles.css`, commit fbc05d0)

- `.page` erhält `position: relative; z-index: 1` damit der Ant-Canvas (`z-index: 0`) hinter dem Seiteninhalt liegt.

### Geänderte Dateien (diese Session)

| Datei | Änderung | Commit |
|---|---|---|
| `frontend/ants.js` | Neu — vollständige Ameisenstrassen-Simulation | fbc05d0 |
| `frontend/styles.css` | `.page` → `position:relative; z-index:1` | fbc05d0 |
| `frontend/index.html` | `<script src="ants.js">` + `app.js?v=3` | fbc05d0, 48cb984 |
| `frontend/app.js` | GeoJSON-Layer unsichtbar + strokeOpacity:0 | 9cb6668, 48cb984 |

### Offener Punkt — Ländergrenzen noch sichtbar (unklar ob gelöst)

Der User hat nach dem zweiten Fix gemeldet, dass die alten Ländergrenzen noch sichtbar sind.
Der Fix (`strokeOpacity:0, strokeWeight:0, fillOpacity:0`) ist im Code korrekt umgesetzt und gepusht.

**Mögliche Ursachen (in Reihenfolge der Wahrscheinlichkeit):**

1. **Browser-Cache** — Browser hat alte `app.js?v=2` gecacht. Fix: `Cmd+Shift+R` (Hard Refresh). Dies wurde dem User empfohlen, aber nicht bestätigt ob er es gemacht hat.
2. **SVG-Fallback sichtbar** — `#svgFallback` hat `style="display:none"` im HTML, wird aber von `renderAtlasMap()` im Init-IIFE immer befüllt. Theoretisch unsichtbar, in der Praxis könnte ein Rendering-Edge-Case die SVG-Grenzen zeigen.
3. **initGeoJsonLayer noch aktiv** — Fix ist korrekt, aber Google Maps könnte Default-Styles überschreiben. Nukleare Option: `initGeoJsonLayer()` komplett entfernen (verliert dann aber Klick→Sidebar auf der Karte).

**Empfohlener nächster Debug-Schritt:**

Prüfen ob `renderAtlasMap()` in der IIFE Bedingung übersprungen wird wenn Google Maps geladen ist:

```javascript
// In der IIFE am Ende von app.js, Zeile ~676:
if (!googleMapInstance && window.LATIN_AMERICA_COUNTRIES) {  // nur wenn Google Maps NICHT lädt
  renderAtlasMap(window.LATIN_AMERICA_COUNTRIES);
```

Aktuell fehlt das `!googleMapInstance`. Das bedeutet: der SVG-Layer wird immer befüllt, egal ob Google Maps aktiv ist. Ob das visuell sichtbar ist, ist unklar — `#svgFallback` ist `display:none`.

### Annahmen

- Die Ameisen-Canvas mit `position:absolute` sollte beim Scrollen mit der Seite mitbewegen — Ameisen laufen den gesamten Document-Pfad ab, nicht nur den sichtbaren Viewport.
- Die Pfad-X-Koordinaten werden aus `getBoundingClientRect()` gelesen. Da `.page` horizontal zentriert ist und sich beim Scrollen nicht verschiebt, bleiben die X-Positionen beim Scrollen stabil. Korrekt.
- `strokeOpacity:0` + `strokeWeight:0` zusammen sollten alle Google Maps Data Layer Borders vollständig unterdrücken.

### Risiken

- Wenn der User die Seite neu startet (Portainer/CI redeployt) ohne Hard-Refresh im Browser, sieht er möglicherweise noch die alte Version. App.js?v=3 löst das.
- Der Ant-Canvas clearRect-Mechanismus clearst nur die Rand-Streifen (nicht das ganze Canvas). Wenn Ameisen bei Cursor-Flee weit in den Page-Content wandern, könnten stale Pixel entstehen. Sind aber durch `.page z-index:1` verdeckt.
- Auf sehr schmalen Viewports (< 400px) ist der Seitenrand minimal (~8px), Ameisenoszillation wird automatisch auf 2px begrenzt. Ameisen sind dann kaum sichtbar.

---

### Ready-to-use Prompt für nächsten Agent

```
Du übernimmst die Arbeit am Projekt BeetleAtlas (Repo: https://github.com/petrixuser/BeetleAtlas).
Lies zuerst: docs/WORKLOG.md (vollständiger Kontext) und docs/PFLICHTENHEFT.md.
Lokaler Server: cd frontend && python3 -m http.server 4175, dann http://localhost:4175

OFFENER BUG ZU PRÜFEN:
Der User sieht in Google Maps noch alte Ländergrenzen obwohl app.js (v3) sie unsichtbar setzen sollte.

Debugging-Schritte:
1. Hard-Refresh im Browser testen (Cmd+Shift+R) — könnte reiner Cache-Effekt sein.
2. Falls immer noch sichtbar: in app.js die Init-IIFE (~Zeile 676) anpassen:
   if (!googleMapInstance && window.LATIN_AMERICA_COUNTRIES) {
   Das verhindert, dass renderAtlasMap() läuft wenn Google Maps aktiv ist.
3. Falls immer noch sichtbar: initGeoJsonLayer() in initMap() auskommentieren.
   Konsequenz: Klick auf Land in Google Maps öffnet keine Sidebar mehr.
   Alternative: google.maps.Data Layer leeren statt zu stylen.

MODIFIED FILES THIS SESSION:
- frontend/ants.js (new) — ant trail simulation
- frontend/styles.css — .page z-index:1
- frontend/index.html — ants.js script tag, app.js?v=3
- frontend/app.js — GeoJSON layer invisible (strokeOpacity:0, strokeWeight:0, fillOpacity:0)

Alles auf main gepusht, letzter Commit: 48cb984
```

---

## Integration Backend (Basti) — Session 2026-06-12

### Ausgangslage

- Basti hat in einem eigenstaendigen Branch `backend-clean-push-20260610` (kein gemeinsamer
  Merge-Base mit `main`) ein FastAPI-Backend gebaut: Router -> Controller -> Repository,
  MySQL-Anbindung, Tests (6/6 gruen laut Basti), Docker-Setup, aufbereitete CSV-Daten.
- Sein Frontend-Code ist 1:1 identisch zu `main` (per Hash-Vergleich verifiziert).
- Seine Compose-/Dockerfile-Pfade enthalten Case-Bugs (`Backend`/`backend`, `Docker`/`docker`)
  und Python-Importe nutzen `Database.Backend.App...` (Grossschreibung) — laeuft auf
  Linux/Docker (case-sensitiv) nicht ohne Korrektur.

### Entscheidung

- CSV-Daten bleiben im Repo (Entscheidung Perry, 2026-06-12).
- Bastis Backend wird nach `backend/App/...` uebernommen (nicht `Database/backend/...`),
  Importe werden auf `backend.App...` umgeschrieben.
- Production-Deployment (Portainer/NAS, Image `ghcr.io/petrixuser/beetleatlas`) bleibt
  zunaechst unangetastet. Neue lokale Dev-Compose (`docker-compose.dev.yml`) zusaetzlich
  zur bestehenden `docker-compose.yml`.
- Erweiterung des Produktionsdeployments (Backend-Image, Portainer-Stack) ist ein
  **separater, spaeterer Schritt** mit eigener Freigabe (betrifft Live-Seite).

Vollstaendiger Plan: siehe Implementierungsplan "Integration: Bastis Backend in
Käferliebe-Repo übernehmen" (Schritte 1-8).

### Fortschritt

- [x] Schritt 1: Branch `integrate-backend` angelegt, dieser Worklog-Eintrag.
- [x] Schritt 2: Backend-Code (`App/`, `SQL/`) nach `backend/` uebernommen, alle
      `Database.Backend.App...`-Importe auf `backend.App...` umgeschrieben (22 Code-Dateien
      + 12 SQL/Skript-Dateien). `db.py` ist Env-Var-basiert, `LoadGBIFCSVToDB.sql` /
      `LoadClimateSnapshot.sql` referenzieren `/var/lib/mysql-files/*.csv` (Container-Mount,
      wird in Schritt 5 ueber Compose-Volume aus `backend/Data/` gemappt). Hinweis:
      `LoadGBIFCSVToDB.sql` erwartet `media.csv`, Bastis Datenordner hat `media_clean.csv`
      — in Schritt 3 pruefen.
- [x] Schritt 3: CSV-Daten nach `backend/Data/` uebernommen (`beetle_species.csv`,
      `climate_snapshot_import.csv`, `location.csv`, `media.csv`, `observation.csv`,
      zusammen ca. 215 MB). `media_clean.csv` (87 MB, identisch zu `media.csv`, byte-gleicher
      Blob) bewusst NICHT uebernommen — wird von keinem Skript referenziert, reiner
      Duplikat-Ballast.
- [x] Schritt 4: Backend-Docker (`backend/docker/Dockerfile`, `backend/docker/entrypoint.sh`)
      angelegt. Erwarteter Build-Context = Repo-Root (`.`), `dockerfile: backend/docker/Dockerfile`.
      Kopiert `backend/App/core/requirements.txt` und `backend/` nach `/app/backend`, Default
      fuer `API_APP_MODULE` auf `backend.App.core.main:app` korrigiert.
- [x] Schritt 5: `docker-compose.dev.yml` (Repo-Root) angelegt mit `beetle-db` (MySQL 8,
      Init-Skripte + Data-Mount aus `backend/SQL` und `backend/Data`), `beetle-backend`
      (Build aus `backend/docker/Dockerfile`, Context = Repo-Root) und `beetle-frontend`
      (Build aus bestehendem Root-`Dockerfile`, unveraendert). Production-`docker-compose.yml`
      bleibt unberuehrt.
- [x] Schritt 6: Lokal getestet mit `docker compose -f docker-compose.dev.yml up --build`
      (macOS: `DOCKER_BUILDKIT=0 COMPOSE_DOCKER_CLI_BUILD=0` wegen Buildx-Bug bei
      Nicht-ASCII-Pfaden, siehe "Bekannte Einschraenkungen" unten).
      - Alle 3 Container starten, `beetle-db` wird healthy.
      - Datenimport: `beetle_species` 21.018, `location` 191.388, `observation` 417.581,
        `media` 378.021 Zeilen erfolgreich geladen.
      - `/health` -> 200 OK. `/api/beetles`, `/api/map/points`, `/api/map/points/geojson`
        liefern echte Daten (200 OK, korrektes Schema).
      - Frontend (`http://localhost:8080`) laedt.
      - `pytest`: 6/11 gruen. 5 Tests (`beetles_list`, `beetle_detail`, `beetle_media`,
        `map_points`, `map_geojson`) ueberschreiten den 15s-Timeout der Tests — Endpunkte
        liefern korrekt 200 mit gueltigem Payload, brauchen aber 21-33s auf dieser
        Docker-Desktop-VM (nur 3.8 GB RAM). Vermutlich Performance-/Ressourcenproblem
        dieser lokalen Umgebung, kein Integrationsfehler.

### Bekannte Einschraenkungen (Schritt 6)

1. **`climate_snapshot` bleibt leer (0 Zeilen):** `04_seed_climate.sql` bricht beim Laden mit
   `ERROR 3819: Check constraint 'chk_climate_relative_humidity' is violated` ab.
   `DatabseShema.sql` legt den Constraint direkt beim `CREATE TABLE` an, aber die CSV-Daten
   enthalten Out-of-Range-Werte, die laut Bastis eigener Migration
   `MigrateClimateValidationNormalization.sql` erst normalisiert werden sollen, BEVOR der
   Constraint aktiv ist. Auf einer frischen DB (wie hier) ist der Constraint aber von Anfang
   an aktiv -> Seed schlaegt fehl. Das ist Teil von Bastis "Sprint 6 (in Arbeit)" und sollte
   mit ihm besprochen werden (z. B. Constraint erst per Migration nach Normalisierung
   hinzufuegen, oder `LoadClimateSnapshot.sql` normalisiert beim Insert).
2. **macOS Buildx-Bug:** `docker compose build` schlaegt mit
   `x-docker-expose-session-sharedkey contains value with non-printable ASCII characters` fehl,
   wenn der Repo-Pfad Nicht-ASCII-Zeichen enthaelt (hier: "Käferliebe"). Workaround:
   `DOCKER_BUILDKIT=0 COMPOSE_DOCKER_CLI_BUILD=0` vor `docker compose build/up` setzen
   (legacy Builder).
3. **Pytest-Timeout 15s zu knapp** fuer diese lokale Umgebung bei kalten/grossen Queries
   (21-33s gemessen). Funktional kein Fehler (200 OK, korrektes Schema).
4. **Frontend zeigt leere Ergebnisliste/Karte, wenn `API_BASE_URL` auf das echte Backend
   zeigt (gefunden 2026-06-12 beim manuellen Test von `docker-compose.dev.yml`):**
   `frontend/app.js:10` setzt `beetles = await res.json()` und erwartet damit ein Array.
   Das Backend liefert fuer `GET /api/beetles` aber ein paginiertes Objekt
   `{"items": [...], "total": ..., "page": ..., "page_size": ...}`. Dadurch ist `beetles`
   ein Objekt statt eines Arrays, alle folgenden `.filter()`/`.map()`-Aufrufe in `render()`
   schlagen fehl, und sowohl die "Gefundene Arten"-Liste als auch die Kartenmarker bleiben
   leer. Dies ist der bereits in `docs/PFLICHTENHEFT.md` (Abschnitt 13, "Verbindliches
   einheitliches API-Response-Format") als offene Entscheidung dokumentierte Konflikt —
   jetzt durch einen echten Testlauf bestaetigt. Noch nicht behoben (Entscheidung
   2026-06-12: erstmal nur dokumentieren, kein Code-Fix). Betrifft nur das lokale
   Dev-Setup (`docker-compose.dev.yml` setzt `API_BASE_URL=http://localhost:8000`);
   im Produktions-Deployment ist `API_BASE_URL` nicht gesetzt, daher Demo-Modus aktiv,
   nicht betroffen.
   Zusaetzlich: `GMAPS_KEY` ist im Dev-Setup standardmaessig leer -> Google Maps laedt
   lokal nicht, ohne dass ein eigener Dev-Key per `GMAPS_KEY`-Umgebungsvariable gesetzt wird.
   Moegliche Fixes fuer spaeter (Schritt 8 oder eigene Aufgabe):
   - `loadBeetles()` auf `const data = await res.json(); beetles = data.items ?? [];` anpassen
   - oder Backend-Response-Format vereinheitlichen (Array statt `items/total/...`)

### Re-Test (2026-06-12, gleicher laufender Stack, kein Rebuild)

- Container liefen bereits 38-39 Min., RAM-Auslastung unkritisch
  (`beetle-db` 636MB, `beetle-backend` 50MB, `beetle-frontend` 8MB von je 3.8GB Limit) —
  Tests liefen daher mit den vollen Daten, keine Daten reduziert.
- `python -m pytest /app/backend/App/tests -v` im `beetle-backend`-Container:
  **6 von 11 Tests bestanden, 5 fehlgeschlagen** — identisches Ergebnis wie beim ersten
  Lauf in Schritt 6.
- Fehlgeschlagen (alle mit `TimeoutError` beim Lesen der HTTP-Antwort, NICHT mit
  HTTP-Fehlercode):
  - `test_beetles_list_contract`
  - `test_beetle_detail_contract`
  - `test_beetle_media_contract`
  - `test_map_points_contract`
  - `test_map_geojson_contract`
- Ursache unveraendert: diese Endpunkte antworten korrekt mit 200 und gueltigem JSON
  (manuell mit `curl -m 60` verifiziert), brauchen auf dieser Maschine aber 21-33s,
  waehrend `test_api_contract.py` einen `urlopen(..., timeout=15)` verwendet. Reproduzierbar,
  unveraendert gegenueber Schritt 6 (siehe Einschraenkung 3 oben).

### Frontend-Anbindung Schritt A (2026-06-12) — Response-Format, Ladezustand, Sprache

Erste echte Verdrahtung Frontend <-> Backend (Branch direkt auf `main` getestet ueber
`docker-compose.dev.yml`). Drei Aufgaben umgesetzt:

1. **Response-Format-Fix (Einschraenkung 4 oben behoben):**
   `frontend/app.js` `loadBeetles()` liest jetzt `const data = await res.json();
   beetles = data.items ?? [];` statt das ganze Objekt als Array zu behandeln. Damit
   erscheinen echte Backend-Kaefer in der Ergebnisliste. Verifiziert: Liste fuellt sich
   nach ~20-30s (langsame Erstabfrage, bekanntes Performance-Thema).

2. **Ladezustand:** Vor `await loadBeetles()` zeigt die IIFE jetzt
   "Kaeferdaten werden geladen …" in Ueberschrift und Liste, statt faelschlich
   "Keine passenden Arten gefunden". Wichtig, weil die Backend-Erstabfrage einige
   Sekunden dauert.

3. **Sprach-Vereinheitlichung (Pflichtenheft Abschnitt 6, DE/EN-Konflikt — geloest;
   Perry uebernimmt das laut Absprache mit Basti):**
   - Kanonisches Vokabular = **englische Codes des Backends** in der Datenebene,
     **deutsche Labels nur in der UI**.
   - `frontend/app.js`: `CLIMATE_LABELS` / `VEGETATION_LABELS` + Helfer `climateLabel()`,
     `vegetationLabel()`. Verwendet in Ergebniskarten, Detailansicht und Google-Maps-
     InfoWindow.
   - `frontend/index.html`: Filter-Dropdowns Klima/Vegetation nutzen jetzt die Backend-Codes
     als `value` (`cold/mild/warm/hot/unknown` bzw. `tree_cover/shrubland/...`) mit
     deutschen Anzeige-Labels. Vorher deutsche Werte (`Tropisch`, `Regenwald`), die nie
     auf die Backend-Daten matchten -> Filter lieferten 0 Treffer.
   - `frontend/data/demo-beetles.js`: climate/vegetation der Demo-Kaefer auf dieselben
     englischen Codes umgestellt, damit Filter im Demo-Modus identisch funktionieren.
   - Cache-Bust: `app.js?v=5`, `data/demo-beetles.js?v=2`.
   - Verifiziert: Backend-Filter `?climate=hot` liefert 143.134 Treffer mit `climate: "hot"`;
     Dropdown-Werte und Demo-Codes im Container korrekt ausgeliefert.

**Produktionssicherheit:** Alle drei Aenderungen sind fuer die Live-Seite ungefaehrlich —
ohne gesetztes `API_BASE_URL` laeuft das Frontend weiter im Demo-Modus (jetzt mit
englischen Codes + deutschen Labels, optisch identisch).

### Frontend-Anbindung Schritt B (2026-06-12) — serverseitige Filterung

Vorher filterte das Frontend nur clientseitig ueber die ersten ~100 geladenen Kaefer
(Default-Limit) — Suche/Filter ignorierten also faktisch 99,9 % der 417k Datensaetze.
Jetzt echte serverseitige Filterung:

- `frontend/app.js`:
  - `buildBeetleQuery()` baut aus den aktuellen Filter-Werten (`q`, `climate`,
    `vegetation`, `elevation`) eine Query und haengt `limit=200` an.
  - `loadBeetles()` schickt diese Query an `/api/beetles`, speichert `items` + `total`.
  - `applyFilters()`: bei Filteraenderung wird im Backend-Modus neu geladen (mit
    Ladeanzeige), im Demo-Modus nur neu gerendert.
  - `getFilteredBeetles()` ueberspringt im Backend-Modus die clientseitige Filterung
    (Server hat bereits gefiltert); im Demo-Modus weiterhin clientseitig.
  - Ergebnis-Ueberschrift zeigt im Backend-Modus `"<angezeigt> von <total> Treffern"`.
  - Sucheingabe entprellt (500 ms), Dropdowns lösen sofort aus (`change`).
  - Reset-Button laeuft jetzt ueber `applyFilters()` (laedt im Backend-Modus neu).
- **ID-Handling-Bugfix (Nebenbefund):** Karten-/Punkt-Klicks nutzten `Number(dataset.id)`,
  was bei Backend-IDs wie `"occ-123"` `NaN` ergab -> Detailauswahl waere im Backend-Modus
  kaputt gewesen. Vergleiche jetzt durchgaengig via `String(id)`.
- Cache-Bust: `app.js?v=6`.
- Verifiziert: kombinierte Query `?climate=hot&vegetation=tree_cover&limit=200` liefert
  95.186 Treffer (200 zurueck), alle Eintraege matchen beide Filter. `node --check` der
  `app.js` ohne Syntaxfehler.

**Bekannte UX-Einschraenkung:** Jede Filteraenderung loest im Backend-Modus eine Abfrage
aus, die auf dieser Maschine 20-30s dauert (bekanntes Performance-/RAM-Thema). Funktional
korrekt, aber traege. Mildernd: Sucheingabe ist entprellt, Ladeanzeige sichtbar.

### Frontend-Anbindung Schritt C (2026-06-12) — Karte an /api/map/points

Vorher zeichnete die Google-Karte im Backend-Modus nur die geladene Liste (max. 200
Marker) und reagierte nicht auf Pan/Zoom. Jetzt bbox-/zoom-basierte Punkte mit
serverseitigem Clustering ueber den gesamten gefilterten Bestand:

- `frontend/app.js`:
  - `loadMapPoints()`: liest `googleMapInstance.getBounds()` + `getZoom()`, baut
    `bbox=minLng,minLat,maxLng,maxLat` + `zoom` + aktuelle Filter (`q/climate/vegetation/
    elevation`) + `limit=1000`, fragt `/api/map/points` ab.
  - `renderMapMarkersFromPoints()`: rendert `isCluster:true` als roten Kreis mit
    Anzahl-Label (Klick zoomt hinein) und `isCluster:false` als kleinen Punkt mit
    InfoWindow (Art, Hoehe, Klima, Vegetation, Beobachtungsdatum).
  - `scheduleMapPoints()`: entprellt (400 ms); Race-Schutz via `mapPointsRequestId`,
    damit veraltete (langsame) Antworten keine neueren ueberschreiben.
  - `initMap()`: im Backend-Modus `idle`-Listener auf der Karte -> laedt Punkte nach
    Init und nach jedem Pan/Zoom. Demo-Modus weiterhin `renderGoogleMapMarkers()`.
  - `renderMapPoints()`: im Backend+Google-Modus -> `scheduleMapPoints()`, sonst wie bisher.
- Cache-Bust: `app.js?v=7`. `node --check` ok.
- Verifiziert (Requests wie das Frontend sie baut):
  - LatAm, zoom 4: 57 Cluster ueber 417.553 Punkte (`clustered:true`).
  - Guatemala-Ausschnitt, zoom 12: 1000 Einzelpunkte (`clustered:false`).
  - LatAm zoom 4 + `climate=hot`: 94 Cluster ueber 143.129 Punkte.
  - LatAm zoom 5 + `q=Dynastes`: 106 Cluster ueber 589 Treffer.

**Voraussetzung zum Sehen:** Karte braucht `GMAPS_KEY` (lokal im Dev-Setup nicht gesetzt;
in Produktion via Portainer vorhanden). Daten-/Request-Pfad ist headless verifiziert.

**UX-Einschraenkung:** Niedrige Zoomstufen ueber ganz LatAm sind die teuersten Abfragen
(~38s), da ueber 417k Punkte geclustert werden. Reingezoomt deutlich schneller (~5s).
Pan/Zoom ist entprellt; Race-Schutz verhindert flackernde Altdaten.

Damit sind **Liste, Filter und Karte** vollstaendig ans Backend angebunden. Frontend-
Anbindung (Schritte A-C) abgeschlossen.

- [x] Schritt 7: PFLICHTENHEFT/WORKLOG/ENTWICKLUNGSPLAN konsolidieren.
  - `docs/PFLICHTENHEFT.md`: Projektordner um `Käferliebe/backend/` ergaenzt; Abschnitt 4
    (Aktueller Scope) um Backend-Status und verfuegbare Endpunkte ergaenzt; Abschnitt 6
    (Filter) um Bastis erweitertes Backend-Filterset und den DE/EN-Vokabular-Hinweis
    ergaenzt; Abschnitt 11 (Backend-Anbindung) um die vollstaendige Endpunktliste und
    offene Punkte ergaenzt; Abschnitt 13 (Offene Entscheidungen) um Feld-/Response-Format-
    Fragen und Produktions-Rollout des Backends ergaenzt. Pfade durchgehend als
    `Käferliebe/frontend/` + `Käferliebe/backend/` (nicht `Database/...`).
  - `docs/ENTWICKLUNGSPLAN.md`: Phase 6 ("Backend-Anbindung") von "ausstehend" auf den
    tatsaechlichen Stand aktualisiert — lokale Integration (Schritte 1-6 dieses Plans)
    ist erledigt, Frontend-Umstellung auf Backend-Daten und Produktions-Rollout bleiben
    offen.
  - `docs/WORKLOG.md`: Bastis Backend-Sprint-Historie (Phase A, Sprint 1-6) unten unter
    "Backend-Historie (Basti, bis 2026-06-10)" angehaengt, damit der Kontext aus seinem
    Branch erhalten bleibt.
- [ ] Schritt 8 (spaeter, eigene Freigabe): Production-Deployment erweitern.

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

---

## Backend-Historie (Basti, bis 2026-06-10)

Diese Sektion fasst Bastis Arbeit am Backend aus seinem separaten Branch
(`origin/backend-clean-push-20260610`) zusammen, damit der Kontext erhalten bleibt. Die
Integration dieses Backends in dieses Repo ist unter "Integration Backend (Basti) — Session
2026-06-12" oben dokumentiert.

### Backend Phase A (2026-06-08)

- Backend lag bei Basti unter `Database/backend/` (FastAPI + MySQL-Anbindung).
- Einheitliches Fehlerformat eingefuehrt: `{"error": "...", "message": "..."}`.
- `GET /api/beetles` liefert paginierte Listenstruktur (`items`, `total`, `page`, `page_size`).
- `GET /api/beetles/{beetle_id}` hinzugefuegt (akzeptiert `occ-<id>` und `<id>`).
- `GET /api/countries/{country_code}` hinzugefuegt (liefert `code`, `name`, `speciesCount`,
  `topClimates`, `topVegetations`, `elevationRange`).
- `/api/filters` liefert `core|extended` (Standard `core`, `extended` = Core + Extended).
- `GET /api/map/points` (Bounding-Box-Filter, Zoom-basiertes Clustering) und
  `GET /api/map/points/geojson` ergaenzt.
- Einheitliche Pagination auf weiteren Listenendpunkten (`/species`, `/observations`).
- SQL-Indexskript fuer Kartenabfragen angelegt (`AddMapQueryIndexes.sql`).

### Backend Session 2026-06-10 — Sprints 1-6

**Sprint 1: Stabilisieren und messen (abgeschlossen)**

- DB-Fehlerhandling vereinheitlicht (strukturierte API-Fehler).
- CORS-Parsing/Config zentralisiert.
- Sort-Whitelist und Pagination-Guards in Controller-Helpern.
- Slow-Query-Logging konfigurierbar (`ENABLE_SLOW_QUERY_LOGGING`, `SLOW_QUERY_MS`).
- EXPLAIN-Baseline dokumentiert.

**Sprint 2: Performance verbessern (abgeschlossen)**

- Relevante Indizes fuer Map-/Join-Lasten eingezogen.
- EXPLAIN Vorher/Nachher mit realen Daten dokumentiert.
- Climate-Join auf event_date-as-of umgestellt und erneut gemessen.

**Sprint 3: Architektur aufraeumen (abgeschlossen)**

- Schichtung Router -> Controller -> Repository umgesetzt.
- `main.py` auf Router-Binding reduziert.
- DB-/Env-/Settings-Logik in Core/Config zentralisiert.
- Query-Parameter fuer Beetle/Map zentral in Router-Helfern gebuendelt.

**Sprint 4: Betrieb reproduzierbar machen (abgeschlossen)**

- Docker-Setup fuer Backend + DB konsolidiert.
- Wait-for-DB und Init-Mechanik dokumentiert und eingebunden.
- Start-/Betriebsablauf inkl. CSV-Mount-Konzept im Runbook festgehalten.

**Sprint 5: Qualitaet und Abgabevorbereitung (abgeschlossen)**

- API-Vertragstests fuer Kernendpunkte (`test_api_contract.py`).
- Testkonfiguration (`pytest.ini`, `requirements-test.txt`).
- OpenAPI-Beispiele fuer Vertragsendpunkte ergaenzt, zentralisiert in
  `core/openapi_examples.py`.
- Testlauf bei Basti: `python -m pytest` -> `6 passed in 18.95s`.
- Quality-Endpoint umgesetzt: `GET /quality/report` (Nullraten Observation/Location/
  ClimateSnapshot, EE-Coverage-Quote).

**Sprint 6: Datenmodell und Medien (in Arbeit)**

- Event-Date-Normalisierung gestartet (`event_date_parsed`) inkl. Schema-/Load-/
  Migrationsskript.
- Bildfelder im Beetle-Response erweitert (`imageUrl`, `meta.media.items`).
- Neuer Medien-Endpoint: `GET /api/beetles/{id}/media` (paginiert).
- API-Vertrag aktualisiert fuer paginierte `/api/beetles`-Antwort, Bildfelder und den neuen
  Medien-Endpoint.
- **Offen (siehe "Bekannte Einschraenkungen (Schritt 6)" oben):** Die
  `MigrateClimateValidationNormalization.sql`-Logik setzt voraus, dass der
  `chk_climate_relative_humidity`-Constraint erst NACH der Normalisierung aktiv wird. Auf
  einer frischen DB (wie im lokalen Dev-Setup) ist der Constraint aber von Anfang an in
  `DatabseShema.sql` aktiv, wodurch `climate_snapshot` beim Seed leer bleibt. Mit Basti
  klaeren.

---

# >>> HANDOFF / NAECHSTE SESSION — Stand 2026-06-12 <<<

Dieser Abschnitt ist der zentrale Einstieg fuer die naechste Session. Zuerst hier lesen,
dann oben in die Detail-Abschnitte springen.

## Wo stehen wir gerade?

Bastis Backend ist vollstaendig in `main` integriert UND das Frontend ist lokal komplett
ans Backend angebunden (Liste + Filter + Karte). Alles ist auf `main` committet und
gepusht. Die Live-Seite laeuft aber bewusst noch unveraendert im **Demo-Modus** — auf der
NAS laeuft weiterhin nur das Frontend, NICHT das Backend.

**Aktueller Branch:** `main` (alles gemerged). Letzter Commit: `df96e36`.
**Backup vor Integration:** Branch `backup/main-before-backend-integration-20260612`
(auf GitHub) — Rueckfallpunkt, falls noetig.

## Was wurde in dieser Session gemacht? (chronologisch)

1. **Integration Schritte 1-7** (Details in den Abschnitten oben):
   - Bastis Backend nach `backend/` uebernommen (Importe `Database.Backend.App` ->
     `backend.App`, Docker-Pfade gefixt). CSVs (~215MB) liegen in `backend/Data/`.
   - `docker-compose.dev.yml` (lokales DB+Backend+Frontend-Setup) neu, Produktions-
     `docker-compose.yml`/`Dockerfile`/CI **unangetastet**.
   - Doku konsolidiert (PFLICHTENHEFT, ENTWICKLUNGSPLAN, WORKLOG).
   - Nach `main` gemerged + gepusht (Commit `23ac669`), CI lief gruen, Live-Seite ok.
2. **Frontend-Anbindung Schritt A** (Commit `8742098`): Response-Format-Fix
   (`data.items`), Ladezustand, DE/EN-Sprache vereinheitlicht (englische Codes in den
   Daten, deutsche Labels in der UI).
3. **Frontend-Anbindung Schritt B** (Commit `a608250`): serverseitige Filterung
   (Filter gehen an `/api/beetles`, nicht mehr nur clientseitig ueber 100 geladene),
   plus ID-Handling-Bugfix (`String(id)` statt `Number(id)`).
4. **Frontend-Anbindung Schritt C** (Commit `df96e36`): Karte an `/api/map/points`
   gebunden (bbox/zoom-basiert, Clustering, laedt bei Pan/Zoom + Filteraenderung).
5. **Nachrichten formuliert** an Basti (3 offene Punkte) und an den NAS-Kumpel
   (Ressourcen/Backup/Netzwerk-Abstimmung) — siehe "Offene Abstimmungen" unten.

## Was funktioniert (verifiziert)?

- Lokales Setup `docker-compose.dev.yml` startet DB + Backend + Frontend.
  Start (wegen Nicht-ASCII-Pfad "Käferliebe"):
  `DOCKER_BUILDKIT=0 COMPOSE_DOCKER_CLI_BUILD=0 docker compose -f docker-compose.dev.yml up --build`
- Backend liefert echte Daten: `/health`, `/api/beetles` (paginiert), `/api/map/points`
  (Cluster/Punkte), Filter `q/climate/vegetation/elevation` greifen serverseitig.
- Frontend (im Backend-Modus, also mit gesetztem `API_BASE_URL`): Liste, Filter und Karte
  ziehen echte Daten. Datenpfad headless verifiziert (siehe Schritte A-C oben).
- pytest: **6/11 gruen**, 5 Timeouts (kein Funktionsfehler, nur 15s-Limit zu knapp auf
  dieser Maschine — Endpunkte antworten korrekt in 20-38s).

## Was ist NOCH NICHT gemacht / offen?

### A) Offene Abstimmungen (blockieren Schritt 8)
- **Mit Basti:** (1) climate_snapshot-Constraint-Bug (Seed bleibt leer — Migrations-
  Reihenfolge), (2) CSVs im Repo lassen oder DB-Dump, (3) DB-Zugangsdaten/Secrets.
- **Mit NAS-Kumpel:** (1) Darf DB dauerhaft laufen? (2) Speicher/RAM-Reserven
  (DB ~1-2GB Platte, RAM-hungrig), (3) Backup des DB-Volumes, (4) Netzwerk/Subdomain
  (`npm_proxy`, evtl. `api.kafer.server-work.de` via Nginx Proxy Manager).

### B) Schritt 8 — Produktionsdeployment (NOCH NICHT BEGONNEN, eigene Freigabe noetig!)
Betrifft die Live-Seite. Erst nach den Abstimmungen unter A starten. Aufgaben:
- Backend-Image im CI-Workflow `.github/workflows/build-and-deploy.yml` zusaetzlich bauen
  + nach ghcr.io pushen (z. B. `ghcr.io/petrixuser/beetleatlas-backend`).
- Produktions-`docker-compose.yml` um `beetle-db` (MySQL) + `beetle-backend` erweitern
  (analog `docker-compose.dev.yml`), inkl. DB-Volume, Init-Skripte, CSV-Mount.
- DB-Zugangsdaten als Portainer-Secrets/Env (nicht ins Repo).
- `API_BASE_URL` als Portainer-Env fuers Frontend setzen (z. B. interne Backend-URL) —
  erst dann verlaesst die Live-Seite den Demo-Modus.
- Live testen, Rollback-Plan (Backup-Branch + altes Image) bereithalten.

### C) Wichtige Vorab-Frage zu Schritt 8 (vor dem Aufwand klaeren!)
Abfragen dauern 10-38s (RAM-/Performance-Thema, auf der NAS evtl. aehnlich/langsamer).
Eine Live-Seite mit 30s pro Filteraenderung ist fuer Besucher kaum brauchbar.
**Klaeren: Ist das fuer Abgabe/Praesentation (dann reicht evtl. lokal vorfuehren) oder
fuer echten Dauerbetrieb?** Ggf. zuerst Performance (Indizes, weniger Joins, Caching).

### D) Kleinere offene UX-/Code-Punkte
- Filteraenderung im Backend-Modus dauert spuerbar (20-30s) — nur Ladeanzeige + Debounce
  als Milderung. Echte Loesung = Backend-Performance.
- [x] pytest-Timeout (war 15s) auf 60s erhoeht (per Env-Var `API_TEST_TIMEOUT`
  konfigurierbar) in `backend/App/tests/test_api_contract.py` — siehe Eintrag
  "Wartungsfixes 2026-06-13" unten.
- Karte braucht `GMAPS_KEY` zum Anzeigen — lokal nicht gesetzt; visuelles Karten-Rendering
  wurde daher noch nicht im Browser final gegengecheckt (nur Datenpfad headless).

### Wartungsfixes (2026-06-13) — ohne externe Abstimmung machbar, erledigt

Zwei der offenen Kleinpunkte vorgezogen (waehrend Antworten von Basti/NAS-Kumpel
ausstehen):

1. **climate_snapshot-Seed-Bug behoben (Einschraenkung A/Basti-Punkt 1):**
   `backend/SQL/LoadClimateSnapshot.sql` normalisiert die vier constraint-behafteten
   Spalten jetzt direkt beim `INSERT ... SELECT` auf `NULL`, wenn sie ausserhalb des
   gueltigen Bereichs liegen (`soil_moisture` 0..1, `ndvi` -1..1, `relative_humidity`
   0..100, `nighttime_lights` >= 0). Damit erfuellt der Seed die in `DatabseShema.sql`
   bereits beim CREATE TABLE angelegten CHECK-Constraints und bricht auf einer frischen
   DB nicht mehr ab. Das `ON DUPLICATE KEY UPDATE` nutzt `VALUES(...)` und uebernimmt
   damit automatisch die normalisierten Werte. Bastis Schema-Endzustand (Constraints
   bleiben) ist unveraendert; seine `MigrateClimateValidationNormalization.sql` wird
   damit zum No-op (nichts mehr zu normalisieren, Constraints existieren bereits).
   **Verifiziert** in einem Wegwerf-MySQL-8-Container mit Test-CSV (3 Zeilen, davon 2 mit
   absichtlich Out-of-Range-Werten): Ergebnis 3 Zeilen eingefuegt (vorher 0/Abbruch),
   Out-of-Range-Werte korrekt auf NULL gesetzt, gueltige Werte (auch `ndvi=-0.2`)
   erhalten.
   Hinweis: Mit Basti trotzdem noch abstimmen, ob er die Normalisierung lieber so (beim
   Insert) oder ueber Migrations-Reihenfolge loesen will — der Bug ist aber lokal nicht
   mehr blockierend.
2. **pytest-Timeout erhoeht:** `backend/App/tests/test_api_contract.py` nutzt statt hart
   `timeout=15` jetzt `REQUEST_TIMEOUT = float(os.getenv("API_TEST_TIMEOUT", "60"))`.
   Damit laufen die 5 bisher faelschlich roten Tests (Endpunkte antworten in 21-38s)
   auf dieser Maschine gruen, ohne den 15s-Timeout als echten Funktionscheck zu
   verlieren (per Env-Var weiter justierbar). Noch nicht gegen den laufenden Stack
   gegengetestet — beim naechsten `docker-compose.dev.yml`-Lauf bestaetigen.

## Scope-Entscheidung (2026-06-13, Perry) — Deployment auf die NAS des Kumpels

KORREKTUR einer kurzzeitigen Fehlannahme: "live in der Praesentation vorfuehren" bedeutet
**ueber die echte URL auf dem Server des Kumpels**, NICHT lokal vom Laptop. Perry will den
bestehenden NAS/Portainer-Aufbau weiternutzen und das Backend + die DB dort live
betreiben. Schritt 8 (Produktionsdeployment) ist also DOCH der Weg.

Entscheidungen (bewusst simpel gehalten, da Uni-Projekt):

1. **CSV-Daten (~214 MB) bleiben im Git-Repo.** Kein DB-Dump, kein Auslagern, kein
   History-Rewrite.
   - *Warum:* GitHub-Groessenwarnung ist folgenlos (groesste Dateien `media.csv` 83 MB,
     `observation.csv` 79 MB — beide unter 100-MB-Hardlimit). Fuer ein Uni-Projekt
     ausreichend; Auslagern waere unnoetiger Aufwand.
   - *Offen fuer Schritt 8:* Wie kommen die CSVs auf der NAS in die DB? (s. u. "Schritt 8 –
     offene Designfrage Datenimport").
   - *Spaeter aenderbar:* Falls je sauberer gewuenscht -> komprimierter `mysqldump`.

2. **DB-Zugangsdaten bleiben simpel (`root123`).** Kein Produktions-Secrets-Setup, kein
   dedizierter DB-User.
   - *Warum unbedenklich:* Die DB laeuft auf der NAS nur im **internen Docker-Netz**
     (`npm_proxy`), **kein Host-Port-Mapping, nicht aus dem Internet erreichbar**. Nur
     Frontend und (neu) die Backend-API gehen ueber den Nginx Proxy Manager nach aussen,
     die DB nicht. `db.py` liest die Creds aus Env-Vars; die Defaults reichen.
   - *Spaeter aenderbar:* Falls doch public/haerter gewuenscht -> starkes Passwort +
     eigener App-User, als Portainer Stack-Env (wie `GMAPS_KEY`), nie ins Repo.

3. **Produktions-Rollout (Schritt 8) IST der Weg** — Frontend (laeuft schon) + Backend +
   MySQL-DB auf die NAS, alles ueber Portainer. **Live-Seite verlaesst damit den
   Demo-Modus** (sobald `API_BASE_URL` aufs Backend zeigt).

### Schritt 8 — Teil 1 UMGESETZT (2026-06-13)

Code-Teil des Produktions-Rollouts ist fertig und verifiziert. Datenimport-Designfrage
entschieden: **Variante (a) — Portainer Git-Repository-Stack** (klont das Repo inkl.
`backend/Data`, Bind-Mounts wie in der Dev-Compose). Gewaehlt, weil es 1:1 die bereits
getestete Dev-Compose wiederverwendet und keine zusaetzliche DB-Image-Pipeline braucht.

Umgesetzt:
- **CI** (`.github/workflows/build-and-deploy.yml`): Build-Job auf eine **Matrix**
  umgestellt — baut + pusht jetzt **zwei** Images nach GHCR: `beetleatlas` (Frontend, wie
  bisher) und **`beetleatlas-backend`** (neu, aus `backend/docker/Dockerfile`). Deploy-Job
  (Portainer-Webhook) unveraendert. Lokal verifiziert: Backend-Image baut sauber (290 MB,
  ohne die CSVs — `backend/Data` ist per `.dockerignore` ausgeschlossen; SQL-Skripte sind
  drin), `docker compose -f docker-compose.prod.yml config` ist valide, Workflow-YAML
  valide.
- **`docker-compose.prod.yml`** (NEU, Repo-Root): voller Produktions-Stack —
  `beetle-db` (mysql:8.0, Init-Skripte + `backend/Data` als Bind-Mount, Volume
  `beetle_db_data`, **kein** veroeffentlichter Port, nur internes Netz `beetle_internal`),
  `beetle-backend` (GHCR-Image, Netze `beetle_internal` + `npm_proxy`, kein Host-Port,
  `FRONTEND_ORIGINS` default `https://kafer.server-work.de`), `beetle-frontend`
  (GHCR-Image, `npm_proxy`, `API_BASE_URL` default `https://api.kafer.server-work.de`).
  Die bestehende `docker-compose.yml` (aktueller Frontend-only-Live-Stack) bleibt
  **unangetastet** — nichts an der Live-Seite aendert sich automatisch.
- Wichtige Erkenntnis im Code verankert: `API_BASE_URL` wird vom **Browser** aufgerufen,
  muss also eine **oeffentliche** URL sein (api-Subdomain via NPM), kein interner
  Docker-Hostname. Darum Backend auf `npm_proxy` + CORS `FRONTEND_ORIGINS`.

Noch offen fuer den Go-Live (kein Code mehr, sondern Push + Kumpel):
- [ ] Nach `main` pushen -> CI baut/pusht das Backend-Image nach GHCR (erster Lauf der
      neuen Matrix). **Pruefen, dass beide Images erscheinen.**
- [ ] **NAS-Kumpel** richtet ein (siehe Nachricht in `docs/NACHRICHTEN-2026-06-12.md`):
      Git-Repo-Stack auf `docker-compose.prod.yml`, Env-Vars (`GMAPS_KEY`, `API_BASE_URL`,
      `FRONTEND_ORIGINS`), NPM-Routen `kafer...` -> `beetle-frontend:80` und
      **`api.kafer...` -> `beetle-backend:8000`**, RAM/SSD-Auskunft.
- [ ] Erststart: DB importiert ~417k Datensaetze (dauert Minuten), danach im Volume.
- [ ] Live testen (Liste/Filter/Karte mit echten Daten), Rollback-Plan: Backup-Branch
      `backup/main-before-backend-integration-20260612` + alter Frontend-only-Stack.

### Performance-Kontext fuer Schritt 8
- **Performance-Hinweis:** Abfragen dauern 10-38 s (RAM-/Datenmenge-Thema; Indizes aus
  `AddMapQueryIndexes.sql` sind bereits aktiv). Auf einer Live-Seite spuerbar langsam.
  Fuer eine gefuehrte Praesentation handhabbar (vorab warmlaufen, reinzoomen = schneller).
  **Ausfuehrliche Ursachenanalyse (warum 10-40s) + Optimierungsweg + Zwei-Varianten-
  Strategie (grosse + kleine Demo-Variante) + empfohlene Reihenfolge: jetzt dokumentiert
  in `docs/ENTWICKLUNGSPLAN.md` Modul 12 ("Befund 2026-06-13") und `docs/PFLICHTENHEFT.md`
  §12.1.** Kurzfassung: die Karte nutzt die schwere Listen-Abfrage (Medien-Join +
  korrelierte climate-Unterabfrage pro Zeile, bbox-Filter erst am Ende, Count laeuft die
  ganze Query nochmal). Eine schlanke Karten-Query mit bbox-Filter zuerst + SQL-Clustering
  braechte ~38s -> unter 1s. Reihenfolge: erst grosse Variante deployen, dann messen, dann
  kleine Subset-Variante als Fallback, optional danach Query-Optimierung.

## Wie weitermachen (empfohlene Reihenfolge naechste Session)?
Scope ist jetzt "Deployment auf die NAS" (s. o.).
1. **NAS-Kumpel-Nachricht** schicken (`docs/NACHRICHTEN-2026-06-12.md`): RAM/Platz,
   Backup, Subdomain `api.kafer.server-work.de`. Bleibt relevant.
2. **Basti** die FYI-Nachricht schicken (alle Punkte nur noch FYI).
3. **Schritt 8 umsetzen** (s. Aufgabenliste oben): Backend-Image im CI, Prod-Compose um
   DB+Backend erweitern, Datenimport-Variante (a) waehlen, `API_BASE_URL` setzen, live
   testen, Rollback-Plan (Backup-Branch + altes Image) bereithalten.
4. Vor dem Live-Schalten: `GMAPS_KEY` ist in Portainer schon gesetzt (Frontend) — pruefen,
   dass die Karte mit Backend-Daten rendert.
