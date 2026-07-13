"""Dieses Modul initialisiert die FastAPI-Anwendung, richtet die CORS-Middleware ein
und definiert globale Exception-Handler."""

import asyncio
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException
import logging
from backend.config.settings import parse_allowed_origins, validate_runtime_security
from backend.controllers.beetle_controller import warm_environment_ranges_cache
from backend.controllers.map_controller import warm_map_points_cache
from backend.routers import auth_router, beetle_router, beetle_write_router, core_router, map_router

validate_runtime_security()
app = FastAPI(title="Beetle API", version="1.0.0")
logger = logging.getLogger("beetle.backend.api")


app.add_middleware(
    CORSMiddleware,
    allow_origins=parse_allowed_origins(),
    allow_origin_regex=r"^https?://(localhost|127\.0\.0\.1)(:\d+)?$",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def warm_environment_ranges_on_startup():
    """Fuehrt teure Cache-Warmups im Hintergrund aus, damit die API Healthchecks sofort beantworten kann."""

    async def _warm_caches_background() -> None:
        """Waermt Umweltbereichs- und Kartenpunkt-Cache im Hintergrund-Thread."""
        try:
            await asyncio.to_thread(warm_environment_ranges_cache, force=True)
        except Exception:
            logger.exception("Background warm_environment_ranges_cache failed")
        try:
            await asyncio.to_thread(warm_map_points_cache)
        except Exception:
            logger.exception("Background warm_map_points_cache failed")

    asyncio.create_task(_warm_caches_background())

@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException):
    """Gibt normalisierte JSON-Fehler fuer FastAPI-HTTP-Exceptions zurueck."""
    if isinstance(exc.detail, dict):
        error = exc.detail.get("error", "http_error")
        message = exc.detail.get("message", "Unknown error.")
    else:
        error = "http_error"
        message = str(exc.detail)
    return JSONResponse(status_code=exc.status_code, content={"error": error, "message": message})

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, __: RequestValidationError):
    """Gibt eine standardisierte 422-Validierungsfehler-Antwort zurueck."""
    return JSONResponse(
        status_code=422,
        content={"error": "validation_error", "message": "Ungueltige Anfrageparameter."},
    )

@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(_: Request, exc: SQLAlchemyError):
    """Gibt eine 503-Antwort zurueck, wenn Datenbankoperationen fehlschlagen."""
    logger.exception("Database error handled as 503: %s", exc)
    return JSONResponse(
        status_code=503,
        content={
            "error": "database_unavailable",
            "message": "Datenbank derzeit nicht verfuegbar. Bitte spaeter erneut versuchen.",
        },
    )

@app.exception_handler(StarletteHTTPException)
async def starlette_http_exception_handler(_: Request, exc: StarletteHTTPException):
    """Behandelt Starlette-HTTP-Exceptions mit dem API-Fehler-Envelope."""
    if exc.status_code == 404:
        return JSONResponse(
            status_code=404,
            content={"error": "not_found", "message": "Route nicht gefunden."},
        )

    message = str(exc.detail) if exc.detail else "HTTP error."
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": "http_error", "message": message},
    )

#bindet die API-Router fuer Kernfunktionen, kaeferbezogene Endpunkte und kartenbezogene Endpunkte in die FastAPI-Anwendung ein und macht deren Routen fuer eingehende Anfragen verfuegbar.
app.include_router(core_router)
app.include_router(beetle_router)
app.include_router(beetle_write_router)
app.include_router(map_router)
app.include_router(auth_router)
