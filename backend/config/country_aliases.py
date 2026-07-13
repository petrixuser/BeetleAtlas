"""Laender-Aliasse: Anzeigename <-> ISO2.

Hintergrund: Die DB speichert Laender GEMISCHT — grosse Laender als Name
("Brazil", "Bolivia"), kleinere als ISO2-Code ("GY", "JM", "HT", "SR", ...).
Damit ein Laenderfilter unabhaengig von der Schreibweise greift (und mit dem
Laender-Panel uebereinstimmt), matchen wir beide Varianten.
"""
from __future__ import annotations

from typing import List, Optional

# Anzeigename (GROSSBUCHSTABEN) -> ISO2
COUNTRY_NAME_TO_ISO = {
    "ARGENTINA": "AR",
    "BELIZE": "BZ",
    "BOLIVIA": "BO",
    "BRAZIL": "BR",
    "CHILE": "CL",
    "COLOMBIA": "CO",
    "COSTA RICA": "CR",
    "CUBA": "CU",
    "DOMINICAN REPUBLIC": "DO",
    "ECUADOR": "EC",
    "EL SALVADOR": "SV",
    "FRENCH GUIANA": "GF",
    "GUATEMALA": "GT",
    "GUYANA": "GY",
    "HAITI": "HT",
    "HONDURAS": "HN",
    "JAMAICA": "JM",
    "MEXICO": "MX",
    "NICARAGUA": "NI",
    "PANAMA": "PA",
    "PARAGUAY": "PY",
    "PERU": "PE",
    "PUERTO RICO": "PR",
    "SURINAME": "SR",
    "URUGUAY": "UY",
    "VENEZUELA": "VE",
}

# ISO2 -> Anzeigename (Original-Schreibweise) fuer den Rueck-Lookup.
ISO_TO_DISPLAY_NAME = {iso: name.title() for name, iso in COUNTRY_NAME_TO_ISO.items()}


def country_filter_candidates(value: Optional[str]) -> List[str]:
    """Liefert alle zu matchenden Laenderwerte (Original + ISO2 + Anzeigename).

    So greift der Filter unabhaengig davon, ob die DB das Land als Name oder als
    ISO-Code gespeichert hat. Enthaelt keine Kommata (Laendernamen haben keine),
    daher CSV-kompatibel fuer die bestehende IN-Filterlogik.
    """
    if not value:
        return []
    raw = str(value).strip()
    if not raw:
        return []
    candidates = [raw]
    upper = raw.upper()
    iso = COUNTRY_NAME_TO_ISO.get(upper)
    if iso and iso not in candidates:
        candidates.append(iso)
    display = ISO_TO_DISPLAY_NAME.get(upper)  # falls value bereits ein ISO-Code ist
    if display and display not in candidates:
        candidates.append(display)
    return candidates
