from typing import Any, Dict, List, Optional

from backend.config.beetle_filters import FILTER_COLUMN_MAP


def apply_exact_filters(filters: List[str], params: Dict[str, Any], requested_filters: Dict[str, Optional[str]]) -> None:
    """Apply exact-match SQL filters from requested filter values."""
    for key, column in FILTER_COLUMN_MAP.items():
        value = requested_filters.get(key)
        if value:
            filters.append(f"{column} = :{key}")
            params[key] = value
