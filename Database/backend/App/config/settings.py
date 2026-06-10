import os
from typing import List


def parse_allowed_origins() -> List[str]:
    raw_origins = os.getenv("FRONTEND_ORIGINS", "http://localhost:5173,http://localhost:8080")
    origins = [origin.strip() for origin in raw_origins.split(",") if origin.strip()]
    return origins or ["http://localhost:5173"]
