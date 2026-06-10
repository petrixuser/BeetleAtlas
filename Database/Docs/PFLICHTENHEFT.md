# Pflichtenheft: Beetle Box

Dieses Dokument ist die Single Source of Truth fuer das Frontend des Datenbankenprojekts
"Beetle Box". Wenn Anforderungen unklar sind oder sich widersprechen, gilt dieses Dokument
als verbindliche Grundlage und muss zuerst aktualisiert werden.

Projektordner:

- `Database/frontend/`
- `Database/backend/`

## 1. Projektziel

Beetle Box ist ein Frontend fuer den "Latin Americas Beetle Atlas".

Ziel ist eine uebersichtliche Weboberflaeche, mit der Nutzer Kaeferarten in Lateinamerika
suchen, filtern und raeumlich auf einer Karte betrachten koennen.

Die Anwendung soll spaeter mit einem Backend verbunden werden, das Daten aus einer
relationalen Datenbank liefert.

## 2. Zielgruppe

Die Anwendung richtet sich primaer an:

- Studierende
- Forschende
- interessierte Nutzerinnen und Nutzer

Eine Rollenverwaltung ist aktuell nicht geplant.

## 3. Grundprinzipien

- Die Oberflaeche soll schlicht, uebersichtlich und nicht ueberladen sein.
- Die Karte ist der zentrale visuelle Bestandteil der Anwendung.
- Aesthetik und Lesbarkeit sind wichtiger als maximal wissenschaftliche Detailtiefe.
- Komplexe Umweltinformationen sollen spaeter vereinfacht und verstaendlich dargestellt werden.
- Das Frontend greift nicht direkt auf die Datenbank zu, sondern spaeter ueber ein Backend/API.

## 4. Aktueller Scope

Der aktuelle Fokus liegt auf einem integrierten Frontend- plus Backend-MVP.

Aktuell umgesetzt:

- Frontend in `Database/frontend/`
- Header mit Projektname und Untertitel
- Suchfeld fuer Arten
- Filter fuer Klimazone
- Filter fuer Vegetation
- Filter fuer Hoehenlage
- Ergebnisliste mit Demo-Daten und Backend-Daten (Fallback-Logik)
- Detailbereich fuer ausgewaehlte Kaeferart
- Google-Maps-2D-Karte als primaere Kartenansicht
- Umschaltbare Kartenebenen fuer Hoehe, Klima und Vegetation (Overlay-Stand)
- Echte GeoJSON-Laendergrenzen fuer Lateinamerika
- Klickbare Laenderinformationen ueber GeoJSON-Layer
- Rechte Seitenleiste fuer Laenderinformationen
- Marker-/Popup-Darstellung fuer Kaeferpunkte auf der Karte
- Backend in `Database/backend/` mit FastAPI und MySQL-Anbindung
- Verfuegbare API-Endpunkte: `/health`, `/stats/overview`, `/species`, `/observations`, `/climate/location/{location_id}`
- Frontend-nahe API-Endpunkte: `/api/beetles`, `/api/filters`, `/api/field-mappings`

Noch nicht final umgesetzt:

- Vollstaendige Laenderinformationen
- API-Endpunkt gemaess Zielvertrag: `/api/map/points`
- Einheitliche Produktions-Filterung mit serverseitigem Clustering/Aggregation fuer grosse Kartenabfragen
- Vollstaendige Performance-Strategie fuer Millionen von Datensaetzen
- 3D-Kartenansicht fuer Lateinamerika
- Animierte Ameisenstrasse als dekoratives UI-Element

## 5. Header

Der Header soll aktuell folgenden Text enthalten:

- Haupttitel: `Beetle Box`
- Untertitel: `Latin Americas Beetle Atlas`
- Claim: `Find your favorite Beetles`

## 6. Filter

Aktuelle Frontend-Filter (UI):

- Art suchen
- Klimazone
- Vegetation
- Hoehenlage

Aktuelle Klimazonen im Frontend:

- Alle
- Tropisch
- Subtropisch
- Trocken
- Gebirge
- Gemaessigt

Aktuelle Vegetationen im Frontend:

- Alle
- Regenwald
- Savanne
- Trockenwald
- Gebirgsvegetation
- Grasland
- Mangroven

Aktuelle Hoehenlagen im Frontend:

- Alle
- 0-500 m
- 500-1500 m
- 1500-3000 m
- ueber 3000 m

Aktuelle Backend-Filter auf `/api/beetles`:

- `q`, `climate`, `vegetation`, `elevation`
- `temperature_band`, `precipitation_band`, `soil_moisture_band`, `ndvi_band`
- `humidity_band`, `pressure_band`, `light_pollution_band`, `slope_band`
- `water_distance_band`, `human_impact_band`, `landcover_group`
- `coordinate_uncertainty_band`, `soil_ph_band`, `soil_carbon_band`
- `worldclim_temp_band`, `worldclim_precip_band`
- `event_date_quality`, `basis_of_record_class`, `taxon_resolution`
- `media_coverage`, `license_class`
- `limit`, `offset`

Hinweis zur Harmonisierung:

- Frontend-UI arbeitet aktuell mit deutschsprachigen Hauptkategorien (z. B. `Tropisch`),
  Backend-Filteroptionen aus `/api/filters` enthalten zusaetzlich englisch codierte Band-Klassen.
  Diese Vokabular-Mischung muss vor Finalisierung vereinheitlicht werden.

## 7. Karte

Die aktuelle Karte nutzt Google Maps als Hauptansicht, mit lokaler SVG-/GeoJSON-Karte als Fallback.

Zielarchitektur: Google Maps API ist das technische Grundgeruest fuer Fundpunkte, Filter und
spaetere Kartenebenen.

Mindestanforderung:

- Lateinamerika soll mit moeglichst genauen Umrissen sichtbar sein.
- Laendergrenzen muessen klar erkennbar sein.
- Laendernamen sollen sichtbar sein.
- Die Karte soll interaktiv sein.
- Nutzer sollen zoomen und verschieben koennen.
- Die spaetere Google-Maps-Karte soll als zentrale Kartenkomponente genutzt werden.
- Kaeferfundorte aus dem Backend sollen spaeter als Punkte auf der Karte angezeigt werden.

Aktuelle technische Umsetzung:

- Die Hauptkarte wird ueber Google Maps gerendert.
- Die Laendergrenzen fuer Interaktionen stammen aus lokalen GeoJSON-Daten.
- Die GeoJSON-Daten liegen in `Database/frontend/assets/latin-america-countries.geojson`.
- Zur robusteren Darstellung in Chrome liegen dieselben Daten zusaetzlich als JS-Datei in
  `Database/frontend/assets/latin-america-countries.js`.
- Die lokale SVG-Karte bleibt als Fallback erhalten.

Aktuelle Interaktion:

- Klick auf einen Laendernamen oeffnet rechts eine Seitenleiste.
- Klick auf einen Kaeferpunkt oeffnet ein kleines Popup auf der Karte.
- Klick auf einen Punkt schliesst die Laender-Seitenleiste.

Ziel-Interaktion fuer Google Maps:

- Standardansicht als normale Google-Maps-2D-Karte.
- Umschaltbare Ansicht per Button fuer 3D-Karte.
- Umschaltbare Kartenebenen fuer Hoehenunterschiede, Klimazonen und Vegetationszonen.
- Popups und Overlays muessen synchron zur Kartenbewegung, zum Zoom und zur Navigation bleiben.
- Kaeferfundpunkte sollen spaeter als kleine Punkte aus Backend-Daten angezeigt werden.

## 8. Seitenleiste

Die rechte Seitenleiste ist fuer Laenderinformationen vorgesehen.

Aktueller Stand:

- Wird nur durch Klick auf einen Laendernamen geoeffnet.
- Zeigt aktuell den Namen des Landes und Platzhaltertext.
- Inhalte sind noch nicht final befuellt.

Spaetere moegliche Inhalte:

- Laendername
- Anzahl gefundener Arten
- typische Klimazonen
- typische Vegetation
- Hoehenbereiche
- auffaellige Fundorte

## 9. Punkt-Popup

Das kleine Popup auf der Karte ist fuer Informationen zu einem Kaeferfundpunkt vorgesehen.

Aktueller Stand:

- Wird durch Klick auf einen Kaeferpunkt geoeffnet.
- Zeigt aktuell Platzhalter fuer Hoehe, Vegetation und Klimazone.

Spaetere moegliche Inhalte:

- Artname
- Fundort
- Hoehe
- Vegetation
- Klimazone
- Temperatur
- Beobachtungsdatum

## 10. Datenmodell Frontend

Aktuell gibt es Demo-Daten und Backend-Datenanbindung in `Database/frontend/app.js`.

Beispieldaten enthalten:

- id
- name
- family
- location
- coordinates
- climate
- vegetation
- elevation
- temperature
- soil

Spaeter sollen diese Daten ueber das Backend geladen werden.

## 11. Backend-Anbindung

Das Frontend kommuniziert bereits ueber HTTP mit dem Backend, falls `window.API_BASE_URL`
gesetzt ist. Ohne Backend-URL wird weiterhin mit Demo-Daten gearbeitet.

Beispiel:

```js
const response = await fetch("http://localhost:8080/api/beetles");
const beetles = await response.json();
```

Das Backend ist verantwortlich fuer:

- Datenbankzugriff
- Filterlogik fuer grosse Datenmengen
- Aggregation von Kartenpunkten
- Bereitstellung von JSON fuer das Frontend
- Bereitstellung der Kaeferfundorte fuer die Google-Maps-Karte
- Bereitstellung der fachlichen Attribute fuer Marker/Popups, z. B. Hoehe, Vegetation,
  Klimazone und Beobachtungsdaten

Bereits vorhanden:

- `/api/beetles` (inkl. breitem Filterset und Pagination ueber `limit`/`offset`)
- `/api/beetles/:id`
- `/api/beetles/:id/media` (paginierte Bild-/Medienliste)
- `/api/countries/:countryCode`
- `/api/map/points` (Bounding-Box, Zoom-basiertes Clustering, Pagination)
- `/api/map/points/geojson`
- `/api/filters`
- `/api/field-mappings`
- Basis-Endpunkte fuer Datenanalyse und Betrieb (`/health`, `/stats/overview`, `/species`,
  `/observations`, `/climate/location/{location_id}`)

Noch offen fuer den Zielzustand:

- Performance-Optimierung fuer Kartenabfragen unter hoher Last
- Finales Frontend-Pattern fuer Detailbildanzeige (Preview + Galerie aus `/api/beetles/:id/media`)

## 12. Umgang mit grossen Datenmengen

Da perspektivisch ueber 2 Millionen Insekten-Datensaetze existieren koennen, darf das Frontend
nicht alle Punkte einzeln ungefiltert rendern.

Spaeter benoetigt:

- Backend-seitige Filterung
- Aggregierte Kartenpunkte
- Clustering oder Rasterzellen
- Pagination oder limitierte Ergebnislisten
- Nachladen je nach Zoomstufe und Kartenausschnitt

## 13. Offene Entscheidungen

- Welche Laender genau als Lateinamerika gelten sollen.
- Ob kleine Laender dauerhaft beschriftet werden oder erst bei Zoom.
- Ob Kaeferpunkte standardmaessig sofort sichtbar sind oder erst nach Filterung/Zoom.
- Ob die Overlay-Datenquellen fuer Hoehe, Klima und Vegetation im aktuellen Stand bleiben
  oder serverseitig vereinheitlicht werden.
- Kanonische Feld- und Klassenbezeichner zwischen Frontend und Backend:
  deutschsprachige Labels vs. englisch codierte Band-Klassen.
- Verbindliches einheitliches API-Response-Format fuer Listenendpunkte
  (`Array` vs. `items/total/page/page_size`).
- Priorisierung der naechsten API-Ausbauschritte
  (z. B. optionaler GeoJSON-Endpunkt, weitere Performance-Verbesserungen).
- Endgueltige Datenfelder fuer die Frontend-Detailansicht (inkl. Meta-/EE-Bands aus dem Backend).
- Welche Google-Maps-SKUs exakt aktiviert bleiben duerfen.
- Wie Kostenlimits, Quotas und Budgetwarnungen im Google-Cloud-Projekt gesetzt werden.
- Ob die 3D-Karte waehrend der Preview-/Testphase wirklich verwendet werden darf.
- Welche technische Umsetzung fuer Klima- und Vegetationszonen verwendet wird:
  eigene Overlays, Backend-generierte Polygone, Rasterdaten oder Google-Maps-Datenebenen.
- Ob die Ameisenstrasse rein dekorativ bleibt oder spaeter Interaktionen/Zustaende anzeigen soll.

## 14. Arbeitsregel

Vor groesseren Aenderungen wird dieses Pflichtenheft geprueft.

Wenn eine neue Anforderung hinzukommt:

1. Anforderung im Pflichtenheft ergaenzen oder aendern.
2. Worklog aktualisieren.
3. Erst danach Code aendern.

## 15. Google Maps API Zielanforderungen

Die bisherige lokale SVG-/GeoJSON-Karte soll kuenftig durch eine Google-Maps-basierte Karte
ersetzt werden.

### 15.1 Grundsatz

- Google Maps API wird das Karten-Grundgeruest der Anwendung.
- Die Kaeferdaten bleiben im Backend und werden spaeter ueber eine API geladen.
- Das Frontend visualisiert diese Backend-Daten auf der Google-Maps-Karte.
- Die lokale GeoJSON-Karte darf als Fallback oder Entwicklungszwischenstand bestehen bleiben,
  ist aber nicht die finale Zielarchitektur.

### 15.2 Kosten- und API-Regeln

- Es duerfen nur Google-Maps-Funktionen genutzt werden, die in der Entwicklungsphase im
  kostenlosen Kontingent bzw. aktuell ohne Kosten nutzbar sind.
- Kostenpflichtige APIs/SKUs duerfen nicht versehentlich aktiviert oder verwendet werden.
- Jede Google-Maps-Funktion muss vor Implementierung auf SKU, Kosten und Free-Usage-Limit
  geprueft werden.
- Keine Nutzung von Places, Routes, Directions, Distance Matrix, Geocoding, Elevation API,
  Street View, Aerial View, Photorealistic 3D Tiles oder anderen Zusatzdiensten ohne
  ausdrueckliche Freigabe.
- Fuer Entwicklung ist zunaechst nur die Kartenanzeige selbst vorgesehen.
- Google Maps Platform benoetigt grundsaetzlich API-Key und Billing-Konfiguration; deshalb
  muessen Quotas, Budgetwarnungen und API-Key-Restriktionen vor produktiver Nutzung gesetzt
  werden.
- User-Interaktionen wie Zoomen und Verschieben der Karte gelten laut Google-Dokumentation
  nicht als eigene Requests; Kartenladungen und API-Aufrufe koennen aber billable events sein.
- Die finale Implementierung muss dokumentieren, welche SKUs durch den Code ausgeloest werden.

### 15.3 API-Key-Regel

- Fuer die Entwicklung wurde ein temporaerer Google Maps API-Key bereitgestellt.
- Dieser Key darf nicht fest in den Code oder in versionierte Dateien geschrieben werden.
- Der Key soll lokal ueber Konfiguration, `.env`, eine nicht eingecheckte Datei oder ein anderes
  nicht-versioniertes Verfahren eingebunden werden.
- Der aktuelle Entwicklungskey ist nur fuer die Testphase gedacht und wird spaeter ersetzt.
- Der Key muss im Google-Cloud-Projekt eingeschraenkt werden:
  - HTTP-Referrer-Einschraenkung fuer erlaubte Entwicklungs-/Projekt-URLs.
  - API-Restriktion auf die konkret benoetigten Google-Maps-APIs.
  - Keine Freigabe fuer fremde APIs, insbesondere keine generativen/AI-APIs.

### 15.4 Zielansichten der Karte

Die Webseite soll spaeter eine 3D-Karte Lateinamerikas anzeigen koennen.

Verbindliche Zielansichten:

- 2D-Standardkarte als Hauptansicht.
- Umschaltbare 3D-Ansicht per Button.
- Umschaltbare Darstellung fuer Hoehe.
- Umschaltbare Darstellung fuer Klimazonen.
- Umschaltbare Darstellung fuer Vegetationszonen.

Die 2D-Ansicht muss als Fallback immer verfuegbar bleiben.

### 15.5 Karten-Interaktion

- Popups und Overlays muessen bei Pan/Zoom stabil mitlaufen.
- Marker und Layer muessen bei Filteraenderungen reaktiv aktualisiert werden.
- Kaeferfundpunkte sollen aus dem Backend geladen und auf der Karte dargestellt werden.

### 15.6 Nicht-Ziele im aktuellen Stand

- Keine direkte Datenbankanbindung aus dem Frontend.
- Keine unkontrollierte Nutzung kostenpflichtiger Google-Maps-Zusatzdienste.
- Keine produktive Nutzung ohne API-Key-Restriktionen und Budgetgrenzen.
