"""Zentrale Importstelle fuer alle API-Router der Anwendung."""

from backend.routers.auth_router import router as auth_router
from backend.routers.beetle_router import router as beetle_router
from backend.routers.beetle_write_router import router as beetle_write_router
from backend.routers.core_router import router as core_router
from backend.routers.map_router import router as map_router

__all__ = ["core_router", "beetle_router", "beetle_write_router", "map_router", "auth_router"]
