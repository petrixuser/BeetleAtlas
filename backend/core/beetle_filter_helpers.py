from typing import Any, Dict, List, Optional

from backend.config.beetle_filters import FILTER_COLUMN_MAP


def apply_exact_filters(filters: List[str], params: Dict[str, Any], requested_filters: Dict[str, Optional[str]]) -> None:
    """Apply exact-match SQL filters from requested filter values."""
    for key, column in FILTER_COLUMN_MAP.items():
        value = requested_filters.get(key)
        if not value:
            continue

        if isinstance(value, str):
            values = [part.strip() for part in value.split(",") if part.strip()]
            if len(values) > 1:
                placeholders = []
                for idx, item in enumerate(values):
                    param_key = f"{key}_{idx}"
                    placeholders.append(f":{param_key}")
                    params[param_key] = item
                filters.append(f"{column} IN ({', '.join(placeholders)})")
                continue
            if len(values) == 1:
                value = values[0]

        filters.append(f"{column} = :{key}")
        params[key] = value
