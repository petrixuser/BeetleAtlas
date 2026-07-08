"""Hilfen zur Aufloesung von Koeppen-Klimacodes in Haupt-/Untertypen."""
from typing import Optional

CLIMATE_MAJOR_CODES = {"A", "B", "C", "D", "E"}


def parent_climate_code(code: str) -> Optional[str]:
    """Liefert den Koeppen-Hauptklimacode (A-E) zu einem Subtyp-Code."""
    if not code:
        return None
    major = code[0].upper()
    if major in CLIMATE_MAJOR_CODES:
        return major
    return None


def is_climate_subtype_code(code: str) -> bool:
    """Behandelt jeden mehrstelligen Koeppen-Code mit A-E-Praefix als Subtyp."""
    major = parent_climate_code(code)
    return major is not None and len(code) > 1
