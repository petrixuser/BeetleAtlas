# Pflichtenheft: Beetle Box

Dieses Dokument ist die Single Source of Truth fuer das Frontend des Datenbankenprojekts
"Beetle Box". Wenn Anforderungen unklar sind oder sich widersprechen, gilt dieses Dokument
als verbindliche Grundlage und muss zuerst aktualisiert werden.

Projektordner:

- `Käferliebe/frontend/`
- `Käferliebe/backend/`

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

Der aktuelle Fokus liegt auf dem Frontend-Grundgeruest.

Aktuell umgesetzt:

- Statische Website in `Käferliebe/frontend/`
- Header mit Projektname und Untertitel
- Suchfeld fuer Arten
- Filter fuer Klimazone
- Filter fuer Vegetation
- Filter fuer Hoehenlage
- Ergebnisliste mit Demo-Daten
- Detailbereich fuer ausgewaehlte Kaeferart
- Atlas-Grundkarte von Lateinamerika
- Echte GeoJSON-Laendergrenzen fuer Lateinamerika
- Zoombare und verschiebbare SVG-Karte
- Klickbare Laendernamen
- Rechte Seitenleiste fuer Laenderinformationen
- Kleine Popups fuer Kaeferpunkte auf der Karte

Zusaetzlich vorhanden (lokal, noch nicht im Produktions-Deployment):

- Backend in `Käferliebe/backend/` mit FastAPI und MySQL-Anbindung
- Verfuegbare API-Endpunkte: `/health`, `/stats/overview`, `/species`, `/observations`,
  `/climate/location/{location_id}`
- Frontend-nahe API-Endpunkte: `/api/beetles`, `/api/beetles/:id`, `/api/beetles/:id/media`,
  `/api/countries/:countryCode`, `/api/map/points`, `/api/map/points/geojson`,
  `/api/filters`, `/api/field-mappings`
- Lokales Dev-Setup ueber `docker-compose.dev.yml` (DB + Backend + Frontend), getestet mit
  echten GBIF-Daten

Noch nicht final umgesetzt:

- Backend-Anbindung im Produktions-Deployment (Portainer/NAS)
- Vollstaendige Laenderinformationen
- Echte Punktinformationen fuer Kaeferfundorte
- Themenkarten fuer Hoehe, Vegetation und Klimazonen
- Performance-Konzept fuer Millionen von Datensaetzen
- Migration der Karte von lokaler SVG-/GeoJSON-Karte zu Google Maps API
- 3D-Kartenansicht fuer Lateinamerika
- Animierte Ameisenstrasse als dekoratives UI-Element

## 5. Header

Der Header soll aktuell folgenden Text enthalten:

- Haupttitel: `Beetle Box`
- Untertitel: `Latin Americas Beetle Atlas`
- Claim: `Find your favorite Beetles`

## 6. Filter

Aktuelle Filter:

- Art suchen
- Klimazone
- Vegetation
- Hoehenlage

Aktuelle Klimazonen:

- Alle
- Tropisch
- Subtropisch
- Trocken
- Gebirge
- Gemaessigt

Aktuelle Vegetationen:

- Alle
- Regenwald
- Savanne
- Trockenwald
- Gebirgsvegetation
- Grasland
- Mangroven

Aktuelle Hoehenlagen:

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
  Backend-Filteroptionen aus `/api/filters` enthalten zusaetzlich englisch codierte
  Band-Klassen. Diese Vokabular-Mischung muss vor Finalisierung vereinheitlicht werden.

## 7. Karte

Die aktuelle Karte ist eine lokale SVG-/GeoJSON-Grundkarte.

Zielarchitektur: Die Karte soll kuenftig auf Google Maps API umgestellt werden.
Die Google-Maps-Karte soll das technische Grundgeruest fuer Fundpunkte, Filter und spaetere
Kartenebenen bilden.

Mindestanforderung:

- Lateinamerika soll mit moeglichst genauen Umrissen sichtbar sein.
- Laendergrenzen muessen klar erkennbar sein.
- Laendernamen sollen sichtbar sein.
- Die Karte soll interaktiv sein.
- Nutzer sollen zoomen und verschieben koennen.
- Die spaetere Google-Maps-Karte soll als zentrale Kartenkomponente genutzt werden.
- Kaeferfundorte aus dem Backend sollen spaeter als Punkte auf der Karte angezeigt werden.

Aktuelle technische Umsetzung:

- Die Karte wird als SVG gerendert.
- Die Laendergrenzen stammen aus lokalen GeoJSON-Daten.
- Die GeoJSON-Daten liegen in `Käferliebe/frontend/assets/latin-america-countries.geojson`.
- Zur robusteren Darstellung in Chrome liegen dieselben Daten zusaetzlich als JS-Datei in
  `Käferliebe/frontend/assets/latin-america-countries.js`.
- Diese Umsetzung ist als Zwischenstand zu verstehen und soll spaeter durch Google Maps ersetzt
  werden.

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

Aktuell gibt es nur Demo-Daten in `Käferliebe/frontend/app.js`.

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

Das Frontend soll spaeter ueber HTTP mit dem Backend kommunizieren.

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

Im lokalen Dev-Setup bereits vorhanden (`Käferliebe/backend/`):

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

Noch offen:

- Anbindung dieser Endpunkte an das Frontend (aktuell laeuft das Frontend im Demo-Modus)
- `API_BASE_URL` im Produktions-Deployment (Portainer) setzen, sobald Backend dort verfuegbar ist
- Kanonische Vereinheitlichung der Filter-Vokabulare (siehe Abschnitt 6)

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
- Ob Kaeferpunkte auf der Grundkarte sofort sichtbar sein sollen.
- Wie die spaeteren Themenkarten fuer Hoehe, Klima und Vegetation aussehen sollen.
- Welche API-Endpunkte das Backend bereitstellt.
- Welche Datenfelder final in der Datenbank existieren.
- Welche Google-Maps-SKUs exakt aktiviert bleiben duerfen.
- Wie Kostenlimits, Quotas und Budgetwarnungen im Google-Cloud-Projekt gesetzt werden.
- Ob die 3D-Karte waehrend der Preview-/Testphase wirklich verwendet werden darf.
- Welche technische Umsetzung fuer Klima- und Vegetationszonen verwendet wird:
  eigene Overlays, Backend-generierte Polygone, Rasterdaten oder Google-Maps-Datenebenen.
- Ob die Ameisenstrasse rein dekorativ bleibt oder spaeter Interaktionen/Zustaende anzeigen soll.
- Kanonische Feld- und Klassenbezeichner zwischen Frontend und Backend:
  deutschsprachige Labels vs. englisch codierte Band-Klassen.
- Verbindliches einheitliches API-Response-Format fuer Listenendpunkte
  (`Array` vs. `items/total/page/page_size`).
- Wie und wann das Backend ins Produktions-Deployment (Portainer/NAS) aufgenommen wird.

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

Per Button soll zwischen folgenden Ansichten gewechselt werden koennen:

- Standard 2D Google-Maps-Ansicht
- 3D-Kartenansicht
- Hoehenunterschiede
- Klimazonen
- Vegetationszonen

Die Standardansicht soll der normalen Google-Maps-Darstellung entsprechen.

Hoehen-, Klima- und Vegetationsansichten koennen spaeter ueber eigene Overlays,
Backend-Polygone, Rasterdaten oder eine andere kostenkontrollierte technische Loesung umgesetzt
werden. Die genaue technische Umsetzung ist noch offen.

### 15.5 Backend-Daten auf der Karte

Die Kaeferfundorte liegen spaeter im Backend.

Die Karte soll diese Fundorte anzeigen:

- als kleine Punkte/Marker
- gefiltert nach Such- und Umweltkriterien
- synchron zur Karte
- performant auch bei sehr grossen Datenmengen

Bei ueber 2 Millionen Insekten-Datensaetzen darf das Frontend nicht alle Punkte ungefiltert
laden oder rendern.

Erforderlich sind spaeter:

- Backend-seitige Filterung
- Aggregation oder Clustering
- Nachladen nach Kartenausschnitt
- Nachladen nach Zoomstufe
- Begrenzte Ergebnislisten

### 15.6 Popup- und Overlay-Verhalten

Die UI soll intuitiv und reaktiv sein.

Wenn ein Popup oder Overlay auf der Karte geoeffnet wird:

- Es muss sich synchron mit Kartenbewegung und Zoom verhalten.
- Es darf nicht losgeloest an einer falschen Bildschirmposition stehen bleiben.
- Es muss klar erkennbar sein, auf welchen Marker oder Kartenpunkt es sich bezieht.
- Es darf die Kartenbedienung nicht unnoetig blockieren.

### 15.7 3D-Kartenhinweis

3D Maps in Google Maps JavaScript ist laut aktueller Google-Dokumentation ein Preview-/Pro-Thema.
Vor der Implementierung muss erneut geprueft werden:

- ob die 3D-Funktion weiterhin kostenlos bzw. im Free-Usage-Rahmen nutzbar ist,
- welche SKU ausgeloest wird,
- ob die Funktion fuer die Projektregion verfuegbar ist,
- ob die Nutzung fuer ein studentisches Projekt vertretbar ist.

## 16. UI-/Designanforderung: Ameisenstrasse

Die Webseite soll spaeter eine kleine animierte Ameisenstrasse als dekoratives UI-Element
bekommen.

Anforderungen:

- Position: am Rand oben links startend.
- Bewegung: langsam am linken Bildschirmrand nach unten, dann nach rechts und rechts wieder nach
  oben.
- Geschwindigkeit: sehr langsam und unaufdringlich.
- Vordergrund: Die Ameisenstrasse soll sichtbar im Vordergrund liegen.
- Kartenregel: Die Ameisenstrasse darf niemals ueber die visuelle Karte laufen.
- Mausinteraktion: Wenn der Mauszeiger den Weg versperrt, sollen die Ameisen ausweichen.
- Die Animation darf die Bedienbarkeit der Website nicht stoeren.
- Die Umsetzung soll performant sein und keine starken Layout-Verschiebungen verursachen.

Noch offen:

- Ob die Ameisenstrasse per CSS, Canvas oder SVG umgesetzt wird.
- Ob sie auf Mobile angezeigt, reduziert oder deaktiviert wird.
- Wie exakt die Kollision mit dem Mauszeiger berechnet wird.
- Wie verhindert wird, dass die Ameisen ueber die Karte laufen, wenn Layout und Viewportgroesse
  variieren.

## 17. Externe Quellen und Kostenpruefung

Vor Umsetzung der Google-Maps-Migration muessen die offiziellen Google-Dokumente erneut
geprueft werden:

- Google Maps JavaScript API Usage and Billing
- Google Maps Platform Pricing
- Google Maps Platform SKU details
- Google Maps API Security Best Practices
- 3D Maps in Maps JavaScript API

Aktueller Recherche-Stand am 2026-06-05:

- Google Maps Platform nutzt ein SKU-/Pay-as-you-go-Modell.
- Maps JavaScript API Kartenladungen koennen als `Dynamic Maps` SKU zaehlen.
- Google nennt Free-Usage-Kontingente pro SKU, aber nicht unbegrenzte kostenlose Nutzung.
- 3D Maps ist laut Google aktuell Preview bzw. gesondert zu pruefen.
- API-Keys sollen mit Application Restrictions und API Restrictions eingeschraenkt werden.
