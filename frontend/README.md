# Neotropical Beetle Atlas Frontend

Dieses Verzeichnis enthaelt ein statisches Frontend-Grundgeruest fuer das Datenbankenprojekt.

## Dateien

- `index.html`: Seitenstruktur
- `styles.css`: Layout und Gestaltung
- `app.js`: Such-, Filter-, Karten- und Detail-Logik

## Backend-Anbindung spaeter

Die Demo-Daten stehen aktuell in `app.js` in der Variable `beetles`.
Spaeter kann dieser Teil durch einen API-Aufruf ersetzt werden, zum Beispiel:

```js
const response = await fetch("http://localhost:8080/api/beetles");
const beetles = await response.json();
```

Das Backend sollte JSON liefern, damit das Frontend die Daten direkt anzeigen kann.
