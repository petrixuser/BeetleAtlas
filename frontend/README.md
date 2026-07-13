# Neotropical Beetle Atlas Frontend

Dieses Verzeichnis enthaelt das statische Frontend fuer Karte, Filter, Auth und
Detailansicht.

## Einstiegspunkte

- `index.html`: Hauptseite mit Karte, Suche, Filtern und Modal-UI
- `detail.html`: Detailseite fuer einzelne Kaefer (`?id=<beetle_id>`)
- `js/pages/app.js`: Hauptlogik (State, Filter, Rendering)
- `js/pages/app.map.data.js`: Kartenabfragen, Cache und Markerdaten
- `js/pages/app.map.bootstrap.js`: Google-Maps-Bootstrap, Fallback und Initialisierung
- `js/pages/detail.js`: Detaildaten, Medien und Detailkarte
- `styles/app.css`: Gemeinsame Styles (Main + Shared Components)
- `styles/detail.css`: Detailseiten-spezifische Styles

## JS-Struktur

- `js/shared/`: Gemeinsame Kataloge und Labels (Klima/Vegetation/Land)
- `js/core/`: Basisfunktionen und Auth-Kernlogik
- `js/ui/`: UI-spezifisches DOM-Wiring (Auth-, Formular- und Effekt-UI)
- `js/pages/`: Seitenspezifische Controller-Logik (`index`, `detail`)

## Ordnerstruktur

- `config/`: Laufzeit-Konfiguration (`config.local.js`) + Vorlage (`config.example.js`)
- `styles/`: Aufgeteilte CSS-Dateien

## Datenquellen

- Primar: Backend ueber `window.API_BASE_URL`
- Fallback/Bootstrapping: `data/demo-beetles.js` und `data/featured-beetles.js`

## Konfiguration

- Lokale Konfiguration in `config/config.local.js` (nicht versioniert)
- Vorlage: `config/config.example.js`
