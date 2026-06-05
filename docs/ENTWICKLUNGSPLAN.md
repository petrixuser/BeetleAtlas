# Entwicklungsplan: Beetle Box

Dieser Entwicklungsplan leitet sich aus `Käferliebe/docs/PFLICHTENHEFT.md` ab.
Das Pflichtenheft bleibt die Single Source of Truth fuer Anforderungen.
Dieser Plan beschreibt, wie die Anforderungen in Module, Phasen und Arbeitspakete umgesetzt
werden sollen.

## 1. Ziel des Entwicklungsplans

Der Plan soll festlegen:

- welche Module entwickelt werden,
- in welcher Reihenfolge sie sinnvoll umgesetzt werden,
- welche Abhaengigkeiten zwischen den Modulen bestehen,
- welche Risiken vorher geklaert werden muessen,
- welche Abnahmekriterien pro Modul gelten.

## 2. Grundstrategie

Die Entwicklung wird in klar getrennte Module aufgeteilt.

Wichtigste Regel:

- Erst Google-Maps-Sicherheits- und Kostenrahmen klaeren.
- Dann Google Maps als Kartenbasis integrieren.
- Danach Daten, Filter, Marker und Interaktionen anbinden.
- Danach 3D und Themenebenen planen.
- Erst spaeter dekorative UI-Features wie die Ameisenstrasse.

Die aktuelle SVG-/GeoJSON-Karte bleibt als Zwischenstand und Fallback erhalten, bis die
Google-Maps-Integration stabil funktioniert.

## 3. Entwicklungsphasen

### Phase 0: Dokumentation und Sicherheitsvorbereitung

Ziel:

- Projektregeln festhalten.
- Google-Maps-Kostenrisiko kontrollieren.
- API-Key-Strategie definieren.

Ergebnis:

- Pflichtenheft, Worklog und Entwicklungsplan sind aktuell.
- API-Key wird nicht in versionierte Dateien geschrieben.
- Google-Cloud-Projekt ist auf erlaubte APIs, Referrer, Quotas und Budgetwarnungen begrenzt.

### Phase 1: Google Maps 2D Grundkarte

Ziel:

- Die bestehende SVG-Karte durch eine Google-Maps-2D-Karte als Hauptkarte ersetzen.

Ergebnis:

- Standardansicht von Lateinamerika in Google Maps.
- Karte ist zoombar und verschiebbar.
- Aktuelle SVG-Karte bleibt optional als Fallback.

### Phase 2: Backend-Datenmodell und API-Vertrag

Ziel:

- Frontend und Backend einigen sich auf Datenformate.

Ergebnis:

- API-Endpunkte fuer Kaefer, Filter und Kartenpunkte sind definiert.
- Mock-Daten koennen durch Backend-Daten ersetzt werden.

### Phase 3: Marker, Popups und Filter

Ziel:

- Kaeferfundorte aus Daten auf der Karte anzeigen.
- Filter beeinflussen Liste und Karte synchron.

Ergebnis:

- Marker/Punkte erscheinen auf Google Maps.
- Popups bleiben synchron mit Karte.
- Filter wirken auf Liste und Karte.

### Phase 4: Kartenansichten und Themenebenen — ABGESCHLOSSEN (2026-06-05)

Ergebnis:

- Hoehenansicht: OpenTopoMap-Kacheln via google.maps.ImageMapType.
  Zoom-adaptiv, weltweit korrekt, kein zusaetzlicher Google-SKU.
- Klimaansicht: Koeppen-Geiger-Polygone (Beck et al. 2023) via google.maps.Data.
  Daten: assets/koppen-latam.geojson (1.6 MB, 1991-2020, 22 Klimaklassen).
- Vegetationsansicht: WWF Ecoregion-Polygone via google.maps.Data.
  Daten: assets/ecoregions-latam.geojson (2.9 MB, 14 Biome).
- Alle Layer werden lazy geladen (nur bei erstem Klick) und danach gecacht.
- Legenden fuer alle drei Ansichten vorhanden.

### Phase 5 (Vorgezogen): CI/CD & Deployment-Infrastruktur — ABGESCHLOSSEN (2026-06-05)

Ergebnis:

- GitHub-Repository: https://github.com/petrixuser/BeetleAtlas (public)
- Docker-Image: ghcr.io/petrixuser/beetleatlas:latest
- Deployment: NAS (server-work.de) via Portainer + Nginx Proxy Manager
- Live-URL: https://kafer.server-work.de
- Pipeline getestet: Build 17s + Webhook 5s, beides HTTP 2xx
- Secrets sicher: GMAPS_KEY nie im Image, PORTAINER_WEBHOOK_URL nur als GitHub Secret

Architektur:
GitHub Push (main) → Actions → Docker Build → ghcr.io → Portainer Webhook → NAS Pull

### Phase 6: Performance fuer grosse Datenmengen

Ziel:

- Die Anwendung wird fuer mehrere Millionen Datensaetze vorbereitet.

Ergebnis (ausstehend):

- Keine ungefilterte Anzeige aller Rohpunkte.
- Backend liefert aggregierte/limitierte Daten.
- Karte nutzt Cluster, Raster oder ausschnittsbasiertes Nachladen.

### Phase 7: 3D-Kartenansicht

Ziel:

- 3D-Prototyp nur nach Kosten-/SKU-Pruefung.

Ergebnis (ausstehend):

- 2D-Standardkarte bleibt immer verfuegbar.
- 3D erst nach dokumentierter Kostenfreigabe.

### Phase 8: UI-Feinschliff und Ameisenstrasse

Ziel:

- Website intuitiver und visuell eigenstaendiger machen.

Ergebnis:

- Animierte Ameisenstrasse laeuft am Rand.
- Ameisen weichen dem Mauszeiger aus.
- Ameisen laufen niemals ueber die Karte.

### Phase 7: Tests, Abnahme und Projektabschluss

Ziel:

- Anwendung stabilisieren und praesentationsbereit machen.

Ergebnis:

- Funktionspruefung im Browser.
- Responsives Layout geprueft.
- Dokumentation aktuell.
- Demo-Szenario fuer Abgabe vorbereitet.

## 4. Module

## Modul 1: Dokumentation und Projektsteuerung

### Ziel

Dieses Modul stellt sicher, dass Anforderungen, Entscheidungen und Fortschritt dauerhaft
nachvollziehbar bleiben.

### Dateien

- `Käferliebe/docs/PFLICHTENHEFT.md`
- `Käferliebe/docs/WORKLOG.md`
- `Käferliebe/docs/ENTWICKLUNGSPLAN.md`
- `Käferliebe/docs/README.md`

### Aufgaben

- Pflichtenheft als verbindliche Anforderungsquelle pflegen.
- Worklog nach relevanten Aenderungen aktualisieren.
- Entwicklungsplan bei neuen Entscheidungen anpassen.
- Offene Entscheidungen sichtbar halten.
- Bei groesseren Aenderungen zuerst Dokumentation aktualisieren.

### Abhaengigkeiten

- Keine technischen Abhaengigkeiten.
- Muss vor allen groesseren Umsetzungen aktuell sein.

### Abnahmekriterien

- Neue Anforderungen stehen im Pflichtenheft.
- Aktueller Arbeitsstand steht im Worklog.
- Naechste Schritte sind im Entwicklungsplan nachvollziehbar.
- Eine neue Session kann anhand der Dokumentation weiterarbeiten.

### Risiken

- Anforderungen koennen sich schleichend aendern.
- Dokumentation kann veralten, wenn sie nicht konsequent gepflegt wird.

## Modul 2: Google-Maps-Sicherheits- und Kosten-Setup

### Ziel

Google Maps soll genutzt werden, ohne unkontrollierte Kosten oder unsichere API-Key-Nutzung zu
erzeugen.

### Aufgaben

- Pruefen, welche Google-Maps-APIs fuer die erste Umsetzung wirklich benoetigt werden.
- Nur die benoetigten APIs aktivieren.
- API-Key per HTTP-Referrer einschraenken.
- API-Key per API-Restrictions einschraenken.
- Quotas und Budgetwarnungen im Google-Cloud-Projekt setzen.
- Dokumentieren, welche SKUs durch den geplanten Code ausgeloest werden.
- Entwicklungskey nicht in das Repository schreiben.

### Erlaubter Minimalumfang fuer Start

- Maps JavaScript API fuer einfache 2D-Kartenanzeige.

### Nicht ohne Freigabe verwenden

- Places API
- Routes API
- Directions API
- Distance Matrix API
- Geocoding API
- Elevation API
- Street View API
- Aerial View API
- Photorealistic 3D Tiles
- Generative/AI APIs

### Abhaengigkeiten

- Google-Cloud-Zugang.
- Temporärer Entwicklungskey.
- Entscheidung, welche lokalen URLs erlaubt werden, z. B. `localhost:4173`.

### Abnahmekriterien

- API-Key ist nicht im Git-Repository gespeichert.
- Key funktioniert nur fuer erlaubte Referrer.
- Key ist auf benoetigte Google-Maps-APIs eingeschraenkt.
- Kosten-/SKU-Pruefung ist dokumentiert.
- Budgetwarnung/Quota-Strategie ist dokumentiert.

### Risiken

- Google Maps ist nicht unbegrenzt kostenlos.
- 3D Maps kann Preview/Pro sein und muss vor Nutzung erneut geprueft werden.
- Ein oeffentlich sichtbarer Frontend-Key kann missbraucht werden, wenn er nicht eingeschraenkt ist.

## Modul 3: Google Maps 2D Grundkarte

### Ziel

Die lokale SVG-/GeoJSON-Karte wird durch eine Google-Maps-2D-Karte als Hauptkarte ersetzt.

### Aufgaben

- Lokale Key-Konfiguration erstellen, ohne Key zu committen.
- Google Maps Script dynamisch oder ueber sichere Konfiguration laden.
- Kartencontainer im Frontend vorbereiten.
- Karte auf Lateinamerika zentrieren.
- Startzoom und Bounds fuer Lateinamerika festlegen.
- Standard Google-Maps-2D-Karte anzeigen.
- Bestehende SVG-Karte als Fallback optional behalten.

### Technische Anforderungen

- Karte muss in Chrome sichtbar sein.
- Karte muss zoombar sein.
- Karte muss verschiebbar sein.
- Karte muss responsive sein.
- Karte darf keine zusaetzlichen kostenpflichtigen Bibliotheken laden.

### Abhaengigkeiten

- Modul 2 abgeschlossen oder mindestens freigegeben.
- Google-Maps-Key lokal verfuegbar.

### Abnahmekriterien

- Google Maps erscheint im Browser.
- Lateinamerika ist beim Start sichtbar.
- Nutzer kann zoomen und verschieben.
- Keine Browser-Konsolenfehler.
- Kein API-Key in versionierten Dateien.

### Risiken

- Key-Konfiguration blockiert Kartenanzeige.
- Billing/Quota-Einstellungen koennen Kartenladungen verhindern.
- Ohne korrektes Setup sieht die Seite fuer andere Teammitglieder leer aus.

## Modul 4: Karten-Fallback und Ladezustaende

### Ziel

Die Anwendung soll verstaendlich reagieren, wenn Google Maps nicht geladen werden kann.

### Aufgaben

- Ladezustand anzeigen, solange Google Maps initialisiert.
- Fehlerzustand anzeigen, wenn Google Maps nicht geladen wird.
- Optional: lokale SVG-Karte als Fallback anzeigen.
- Fehlertexte knapp und verstaendlich halten.
- Worklog-Hinweis fuer haeufige Ladeprobleme aufnehmen.

### Abhaengigkeiten

- Modul 3.

### Abnahmekriterien

- Bei erfolgreichem Laden erscheint Google Maps.
- Bei fehlendem Key oder blockierter API erscheint kein leerer Bereich.
- Fehlerzustand erklaert knapp, was fehlt.
- Layout bleibt stabil.

### Risiken

- Fallback kann von der Zielarchitektur ablenken.
- Zu viele technische Fehlermeldungen koennen Nutzer verwirren.

## Modul 5: Backend-API-Vertrag

### Ziel

Frontend und Backend definieren frueh ein gemeinsames Datenformat.

### Aufgaben

- Endpunkte mit Backend-Kollegen abstimmen.
- JSON-Struktur fuer Kaeferliste definieren.
- JSON-Struktur fuer Kartenpunkte definieren.
- Filterparameter definieren.
- Rueckgabe fuer aggregierte Punkte definieren.
- Fehler- und Ladezustaende definieren.
- Mock-API oder Mock-Datei fuer Frontend-Entwicklung erstellen.

### Vorschlag fuer Endpunkte

- `GET /api/beetles`
- `GET /api/beetles/:id`
- `GET /api/map/points`
- `GET /api/filters`
- `GET /api/countries/:countryCode`

### Vorschlag fuer Kartenpunkt

```json
{
  "id": "occurrence-id",
  "speciesName": "Dynastes hercules",
  "lat": -1.4,
  "lng": -78.2,
  "elevation": 450,
  "climate": "Tropisch",
  "vegetation": "Regenwald",
  "observedAt": "2024-05-12"
}
```

### Abhaengigkeiten

- Backend-Konzept.
- Datenbankmodell.
- Filterkonzept.

### Abnahmekriterien

- Endpunkte sind dokumentiert.
- Beispiel-JSON ist vorhanden.
- Frontend kann mit Mock-Daten dieselbe Struktur nutzen.
- Backend und Frontend arbeiten mit denselben Feldnamen.

### Risiken

- Backend-Datenmodell kann sich aendern.
- Zu grosse Antworten koennen Frontend/Karte ueberlasten.
- Uneinheitliche Feldnamen fuehren zu spaeterem Mehraufwand.

## Modul 6: Datenservice im Frontend

### Ziel

Das Frontend bekommt eine zentrale Datenlogik, die spaeter Mock-Daten durch Backend-Daten
ersetzen kann.

### Aufgaben

- Demo-Daten aus `app.js` herausloesen.
- Einen API-/Data-Service aufbauen.
- Mock-Modus und Backend-Modus trennen.
- Ladezustand einbauen.
- Fehlerzustand einbauen.
- Filterparameter zentral sammeln.

### Abhaengigkeiten

- Modul 5 oder vorlaeufiges Mock-Datenformat.

### Abnahmekriterien

- UI haengt nicht direkt an hart codierten Demo-Daten.
- Mock-Daten koennen weiter genutzt werden.
- Backend-URL kann spaeter konfiguriert werden.
- Fehler beim Laden zerstoeren die Seite nicht.

### Risiken

- Zu fruehe API-Abstraktion kann unnoetig kompliziert werden.
- Zu spaete Trennung macht Backend-Anbindung schwerer.

## Modul 7: Filtermodul

### Ziel

Filter sollen Liste, Backend-Abfragen und Karte konsistent steuern.

### Aktuelle Filter

- Art suchen
- Klimazone
- Vegetation
- Hoehenlage

### Spaetere moegliche Filter

- Temperatur
- Beobachtungszeit
- Land
- Familie
- Gattung
- Zeitraum

### Aufgaben

- Filterzustand zentral verwalten.
- Filter in URL optional abbilden.
- Filter an Backend-Abfragen uebergeben.
- Ergebnisliste und Kartenpunkte gemeinsam aktualisieren.
- Reset-Funktion sauber erhalten.

### Abhaengigkeiten

- Modul 5.
- Modul 6.
- Modul 8.

### Abnahmekriterien

- Filteraenderung aktualisiert Ergebnisliste.
- Filteraenderung aktualisiert Kartenpunkte.
- Reset setzt alle Filter zurueck.
- Keine widerspruechlichen Ergebnisse zwischen Liste und Karte.

### Risiken

- Backend und Frontend koennen Filter unterschiedlich interpretieren.
- Bei zu vielen Filtern wird UI unuebersichtlich.

## Modul 8: Marker, Punkt-Popups und Kartenbindung

### Ziel

Kaeferfundorte werden als kleine Punkte/Marker auf der Google-Maps-Karte angezeigt.

### Aufgaben

- Marker-Daten vom Datenservice laden.
- Marker auf Google Maps rendern.
- Klick auf Marker oeffnet Popup.
- Popup zeigt zunaechst Platzhalter oder echte Felder, sobald vorhanden.
- Popup bleibt an Marker/Kartenposition gebunden.
- Popup schliesst sich sinnvoll bei Kartenbewegung oder neuem Marker.

### Popup-Felder

- Artname
- Hoehe
- Vegetation
- Klimazone
- optional: Beobachtungsdatum
- optional: Temperatur

### Abhaengigkeiten

- Modul 3.
- Modul 5.
- Modul 6.

### Abnahmekriterien

- Marker erscheinen korrekt auf der Karte.
- Marker reagieren auf Filter.
- Popup bewegt sich synchron mit Karte.
- Keine falschen Popup-Positionen nach Zoom/Pan.

### Risiken

- Zu viele Marker machen die Karte langsam.
- Google-Maps-Overlay-Arten koennen unterschiedliche Kosten/Verhalten haben.
- Popups duerfen die Kartenbedienung nicht blockieren.

## Modul 9: Sidebar und Detailinteraktionen

### Ziel

Die rechte Seitenleiste zeigt Informationen zu Laendern oder spaeter ausgewaehlten Kontexten.

### Aktueller Stand

- Klick auf Laendernamen oeffnet Sidebar.
- Inhalt ist Platzhalter.

### Zielzustand

- Sidebar ist visuell sauber.
- Sidebar oeffnet nur bei vorgesehenen Interaktionen.
- Sidebar kann geschlossen werden.
- Inhalte koennen spaeter aus Backend-Daten kommen.

### Aufgaben

- Sidebar-Komponente strukturieren.
- Platzhalterinhalte sauber gestalten.
- Spaeteres Datenmodell fuer Laenderinfos planen.
- Interaktion mit Marker-Popups abstimmen.

### Abhaengigkeiten

- Modul 3 fuer Google-Maps-Laenderinteraktion oder eigene Overlay-Labels.
- Modul 5 fuer spaetere Laenderdaten.

### Abnahmekriterien

- Sidebar oeffnet kontrolliert.
- Sidebar schliesst kontrolliert.
- Sidebar blockiert Karte nicht unnoetig.
- Auf mobilen Viewports bleibt sie nutzbar.

### Risiken

- Laenderlabels auf Google Maps sind nicht ohne Weiteres frei klickbar.
- Es kann noetig sein, eigene Land-Overlays oder Label-Layer zu bauen.

## Modul 10: 2D/3D-Ansichtswechsel

### Ziel

Nutzer koennen zwischen Standard-2D-Karte und spaeterer 3D-Kartenansicht wechseln.

### Aufgaben

- Vor Implementierung 3D Maps SKU/Kosten pruefen.
- Entscheiden, ob 3D in der aktuellen Projektphase erlaubt ist.
- Button fuer Ansichtswechsel vorbereiten.
- 2D-Karte als stabile Standardansicht behalten.
- 3D-Karte nur laden, wenn erlaubt und technisch moeglich.

### Abhaengigkeiten

- Modul 2.
- Modul 3.

### Abnahmekriterien

- 2D bleibt immer verfuegbar.
- 3D wird nur bei erfolgreicher API-/Kostenfreigabe aktiviert.
- Kein automatisches Laden teurer 3D-Dienste ohne Nutzeraktion oder Freigabe.
- Dokumentation nennt ausgeloste SKUs.

### Risiken

- 3D Maps ist Preview/Pro und kann sich aendern.
- 3D kann mehr GPU-Leistung brauchen.
- 3D kann bei manchen Browsern/Geraeten schlechter laufen.

## Modul 11: Themenebenen fuer Hoehe, Klima und Vegetation

### Ziel

Nutzer koennen die Karte nach Umweltinformationen betrachten.

### Ansichten

- Hoehenunterschiede
- Klimazonen
- Vegetationszonen

### Moegliche technische Wege

- Eigene Polygon-Overlays auf Google Maps.
- Backend-generierte GeoJSON-Overlays.
- Rasterdaten oder vereinfachte Kacheln.
- Statische vereinfachte Layer fuer Demo-Zwecke.

### Aufgaben

- Pro Themenebene klären, woher die Daten kommen.
- Daten vereinfachen, damit die Karte lesbar bleibt.
- Legenden gestalten.
- Umschaltung per Button/Segmented Control.
- Kosten der Umsetzung pruefen.

### Abhaengigkeiten

- Modul 3.
- Modul 5.
- Fachliche Datenquellen.

### Abnahmekriterien

- Jede Themenebene ist klar unterscheidbar.
- Legenden sind kurz und verstaendlich.
- Karte bleibt nutzbar.
- Themenebenen loesen keine ungeplanten kostenpflichtigen APIs aus.

### Risiken

- Fachliche Daten koennen sehr komplex sein.
- Zu viele Farben/Layer koennen die Karte ueberladen.
- Google-eigene Elevation API waere nicht ohne Freigabe erlaubt.

## Modul 12: Performance und grosse Datenmengen

### Ziel

Die Anwendung funktioniert perspektivisch mit mehr als 2 Millionen Insekten-Datensaetzen.

### Aufgaben

- Keine ungefilterten Rohdaten ins Frontend laden.
- Kartenpunkte nach Ausschnitt und Zoomstufe laden.
- Clustering oder Aggregation nutzen.
- Ergebnisliste begrenzen.
- Backend-Responses klein halten.
- Debounce fuer Filter- und Kartenbewegungen verwenden.

### Backend-Anforderungen

- Filterung nach Art/Klima/Vegetation/Hoehe.
- Bounding-Box-Filter nach Kartenausschnitt.
- Zoombasierte Aggregation.
- Limitierte Rueckgabemengen.

### Abnahmekriterien

- Frontend bleibt auch bei vielen Daten reaktionsfaehig.
- Karte zeigt aggregierte Daten statt Millionen Einzelmarker.
- API-Antworten sind begrenzt.
- Nutzer sieht Ladezustand bei Nachladen.

### Risiken

- Ohne Backend-Aggregation wird die Karte unbrauchbar.
- Marker-Rendering kann Browser stark belasten.
- Google Maps kann bei zu vielen Overlays langsam werden.

## Modul 13: UI-Layout und Designsystem

### Ziel

Die Website bleibt schlicht, intuitiv und hochwertig.

### Aufgaben

- Layout fuer Header, Filter, Karte, Liste, Sidebar finalisieren.
- Responsive Verhalten fuer Desktop und Mobile definieren.
- UI-Komponenten vereinheitlichen.
- Buttons, Selects, Popups und Sidebar optisch angleichen.
- Kartenbereich als Hauptfokus behandeln.

### Abhaengigkeiten

- Module 3, 7, 8, 9.

### Abnahmekriterien

- Nutzer erkennt sofort Suche, Filter und Karte.
- Karte hat genug Platz.
- Sidebar/Popup ueberdecken nicht unnoetig wichtige Inhalte.
- Mobile Ansicht ist bedienbar.

### Risiken

- Zu viele Steuerungen koennen die UI ueberladen.
- Dekorative Elemente duerfen Karte nicht stoeren.

## Modul 14: Ameisenstrasse

### Ziel

Die Ameisenstrasse wird als dekoratives, aber nicht stoerendes UI-Feature umgesetzt.

### Anforderungen

- Start oben links am Rand.
- Langsame Bewegung entlang des Randes.
- Bewegung nach unten, nach rechts und rechts wieder nach oben.
- Ameisen weichen dem Mauszeiger aus.
- Ameisen bleiben im Vordergrund.
- Ameisen laufen niemals ueber die Karte.

### Moegliche technische Umsetzung

- SVG-Pfad mit animierten Ameisen.
- Canvas-Animation.
- CSS-Animation mit JavaScript fuer Mausausweichlogik.

### Empfohlene Reihenfolge

1. Statischer Pfad ausserhalb der Karte.
2. Langsame Animation.
3. Mausposition erfassen.
4. Ausweichverhalten simulieren.
5. Mobile-Verhalten definieren.

### Abhaengigkeiten

- Finaleres Layout aus Modul 13.
- Genaue Kartenposition im Layout.

### Abnahmekriterien

- Animation ist sichtbar, aber ruhig.
- Karte bleibt komplett frei.
- Mausausweichlogik funktioniert grundlegend.
- Animation verursacht keine starken Performance-Probleme.

### Risiken

- Ausweichlogik kann schnell kompliziert werden.
- Animation kann ablenken, wenn sie zu dominant ist.
- Auf kleinen Screens kann das Feature stoeren.

## Modul 15: Testing und Qualitaetssicherung

### Ziel

Die Anwendung wird regelmaessig geprueft, damit Aenderungen keine bestehenden Funktionen
zerstoeren.

### Testbereiche

- Laden der Seite.
- Kartenanzeige.
- Google-Maps-Initialisierung.
- Filter.
- Marker.
- Popup.
- Sidebar.
- Responsive Layout.
- Browser-Konsole.
- API-Key-Konfiguration.

### Aufgaben

- Manuelle Checkliste erstellen.
- Browser-Test mit Desktop-Viewport.
- Browser-Test mit Mobile-Viewport.
- Konsolenfehler pruefen.
- Lade- und Fehlerzustaende pruefen.
- Worklog nach Tests aktualisieren.

### Abnahmekriterien

- Seite laedt ohne Konsolenfehler.
- Karte ist sichtbar.
- Filter funktionieren.
- Popups und Sidebar funktionieren.
- Mobile Ansicht ist nutzbar.

### Risiken

- Google-Maps-Verhalten kann von Key/Billing/Referrer abhaengen.
- Tests muessen zwischen lokaler und spaeterer Deployment-Umgebung unterscheiden.

## Modul 16: Praesentation und Abgabe

### Ziel

Das Projekt soll nachvollziehbar praesentiert werden koennen.

### Aufgaben

- Kurze Demo-Route definieren.
- Erklaeren, warum Backend statt direktem Datenbankzugriff.
- Architekturdiagramm vorbereiten.
- Wichtigste Funktionen zeigen.
- Bekannte Einschraenkungen ehrlich benennen.
- Naechste Schritte dokumentieren.

### Abnahmekriterien

- Demo kann lokal gestartet werden.
- Ziel der Anwendung ist klar.
- Frontend/Backend-Trennung ist erklaerbar.
- Kartenkonzept ist nachvollziehbar.

## 5. Empfohlene Reihenfolge als Arbeitspakete

### Arbeitspaket 1: Google-Maps-Sicherheitscheck

- Google-Cloud-Projekt pruefen.
- APIs einschraenken.
- Referrer einschraenken.
- Quotas/Budgetwarnungen setzen.
- Ergebnis im Worklog dokumentieren.

### Arbeitspaket 2: Lokale Key-Konfiguration

- Nicht-versionierte Konfigurationsdatei definieren.
- Beispiel-Datei ohne echten Key bereitstellen.
- Frontend so vorbereiten, dass Key lokal geladen wird.

### Arbeitspaket 3: 2D Google Maps einbauen

- Google Maps statt SVG-Karte anzeigen.
- Karte auf Lateinamerika zentrieren.
- Lade- und Fehlerzustand einbauen.

### Arbeitspaket 4: Marker-Mock auf Google Maps

- Demo-Kaeferpunkte auf Google Maps anzeigen.
- Popup an Marker binden.
- Filter mit Marker verbinden.

### Arbeitspaket 5: Backend-API-Vertrag finalisieren

- Endpunkte und Datenfelder mit Backend abstimmen.
- Mock-Daten an API-Format angleichen.

### Arbeitspaket 6: Backend-Anbindung

- Echte Daten laden.
- Lade-/Fehlerzustaende.
- Filterparameter ans Backend geben.

### Arbeitspaket 7: Performance-Konzept

- Bounding Box, Zoom, Clustering/Aggregation definieren.
- Keine Millionen Einzelpunkte im Frontend.

### Arbeitspaket 8: Themenkarten planen

- Hoehenlayer.
- Klimazonenlayer.
- Vegetationslayer.
- Kosten- und Datenquellen pruefen.

### Arbeitspaket 9: 3D-Prototyp nur nach Freigabe

- 3D Maps erneut pruefen.
- Kosten/SKU dokumentieren.
- Prototyp nur bei sicherer Kostenlage.

### Arbeitspaket 10: Ameisenstrasse

- Erst nach stabiler Karte und stabilem Layout.
- Animation ausserhalb der Karte.
- Mausausweichen.

## 6. Kritische Entscheidungen vor der naechsten Code-Umsetzung

Vor der Google-Maps-Migration muessen diese Punkte entschieden oder bestaetigt werden:

- Darf die Maps JavaScript API im Google-Cloud-Projekt aktiviert bleiben?
- Sind API-Key-Restriktionen gesetzt?
- Sind Budgetwarnungen/Quotas gesetzt?
- Welche lokalen URLs sind als Referrer erlaubt?
- Soll die aktuelle SVG-Karte als Fallback erhalten bleiben?
- Soll zuerst 2D gebaut werden, bevor 3D getestet wird?

Empfehlung:

- Erst 2D Google Maps stabil bauen.
- 3D erst spaeter pruefen und nur nach dokumentierter Kostenfreigabe.

## 7. Definition of Done fuer den ersten grossen Meilenstein

Meilenstein: Google Maps 2D Basis

Erfuellt, wenn:

- Google Maps wird auf der Seite geladen.
- Lateinamerika ist beim Start sichtbar.
- API-Key steht nicht im Repository.
- Ladezustand und Fehlerzustand existieren.
- Keine ungeplanten Google-Zusatzdienste werden geladen.
- Worklog nennt aktivierte APIs/SKUs.
- Browser-Konsole zeigt keine Fehler.
- Die alte SVG-Karte ist entweder sauber entfernt oder bewusst als Fallback dokumentiert.
