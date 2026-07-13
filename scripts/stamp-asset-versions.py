#!/usr/bin/env python3
"""Setzt EINE gemeinsame Cache-Version an allen Asset-URLs der Frontend-HTMLs.

Statt in index.html/detail.html jede ``?v=N`` einzeln hochzuzaehlen, schreibt
dieses Skript alle Vorkommen von ``?v=...`` (bei /js/, /styles/, /data/, /assets/)
auf denselben Wert. Aufruf:

    python scripts/stamp-asset-versions.py            # Version = aktueller Zeitstempel
    python scripts/stamp-asset-versions.py 20260708   # feste Version vorgeben

So genuegt beim Ausliefern EIN Bump, damit Browser alle geaenderten Dateien neu laden.
"""
import re
import sys
from datetime import datetime, timezone
from pathlib import Path

# Repo-Root: scripts/ liegt direkt darunter.
REPO_ROOT = Path(__file__).resolve().parents[1]
HTML_FILES = [
    REPO_ROOT / "frontend" / "html" / "index.html",
    REPO_ROOT / "frontend" / "html" / "detail.html",
    REPO_ROOT / "frontend" / "html" / "verify-email.html",
]

# CSS-Entry-Points: deren @import-URLs muessen ebenfalls versioniert werden,
# sonst laedt der Browser geaenderte Teil-CSS (via @import) aus dem Cache.
CSS_ENTRY_FILES = [
    REPO_ROOT / "frontend" / "styles" / "app.css",
    REPO_ROOT / "frontend" / "styles" / "detail.css",
]

# Ersetzt den Wert nach ?v= bis zum naechsten Anfuehrungszeichen/&.
_VERSION_QUERY = re.compile(r'(\?v=)[^"\'&\s]+')

# Findet @import url("pfad") bzw. @import url("pfad?v=alt") -> Gruppe 1 = Pfad.
_CSS_IMPORT = re.compile(r'(@import\s+url\("[^"?]+)(?:\?v=[^"]*)?("\))')


def stamp(version: str) -> None:
    """Schreibt die uebergebene Version in alle ?v=-Query-Parameter (HTML + CSS-@imports)."""
    for path in HTML_FILES:
        if not path.exists():
            print(f"uebersprungen (fehlt): {path}")
            continue
        text = path.read_text(encoding="utf-8")
        new_text, count = _VERSION_QUERY.subn(rf"\g<1>{version}", text)
        path.write_text(new_text, encoding="utf-8")
        print(f"{path.name}: {count} Asset-Versionen auf {version} gesetzt")

    for path in CSS_ENTRY_FILES:
        if not path.exists():
            print(f"uebersprungen (fehlt): {path}")
            continue
        text = path.read_text(encoding="utf-8")
        new_text, count = _CSS_IMPORT.subn(rf"\g<1>?v={version}\g<2>", text)
        path.write_text(new_text, encoding="utf-8")
        print(f"{path.name}: {count} @import-Versionen auf {version} gesetzt")


if __name__ == "__main__":
    # Version aus dem ersten Argument oder als kompakter UTC-Zeitstempel.
    ver = sys.argv[1] if len(sys.argv) > 1 else datetime.now(timezone.utc).strftime("%Y%m%d%H%M")
    stamp(ver)
