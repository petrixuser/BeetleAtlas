from typing import Optional

CLIMATE_MAJOR_CODES = {"A", "B", "C", "D", "E"}


def parent_climate_code(code: str) -> Optional[str]:
    """Return the major Koppen climate code (A-E) for a subtype code."""
    if not code:
        return None
    major = code[0].upper()
    if major in CLIMATE_MAJOR_CODES:
        return major
    return None


def is_climate_subtype_code(code: str) -> bool:
    """Treat any multi-character Koppen code with A-E prefix as subtype."""
    major = parent_climate_code(code)
    return major is not None and len(code) > 1
