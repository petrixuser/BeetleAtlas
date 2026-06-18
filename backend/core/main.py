from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException
from backend.config.settings import parse_allowed_origins
from backend.routers import auth_router, beetle_router, beetle_write_router, core_router, map_router

"""This module initializes the FastAPI application, sets up CORS middleware, and defines global exception handlers"""
app = FastAPI(title="Beetle API", version="1.0.0")


app.add_middleware(
    CORSMiddleware,
    allow_origins=parse_allowed_origins(),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.exception_handler(HTTPException)
async def http_exception_handler(_: Request, exc: HTTPException):
    """Return normalized JSON errors for FastAPI HTTP exceptions."""
    if isinstance(exc.detail, dict):
        error = exc.detail.get("error", "http_error")
        message = exc.detail.get("message", "Unknown error.")
    else:
        error = "http_error"
        message = str(exc.detail)
    return JSONResponse(status_code=exc.status_code, content={"error": error, "message": message})

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, __: RequestValidationError):
    """Return a standardized 422 validation error response."""
    return JSONResponse(
        status_code=422,
        content={"error": "validation_error", "message": "Invalid request parameters."},
    )

@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(_: Request, __: SQLAlchemyError):
    """Return a 503 response when database operations fail."""
    return JSONResponse(
        status_code=503,
        content={
            "error": "database_unavailable",
            "message": "Database is currently unavailable. Please try again later.",
        },
    )

@app.exception_handler(StarletteHTTPException)
async def starlette_http_exception_handler(_: Request, exc: StarletteHTTPException):
    """Handle Starlette HTTP exceptions with the API error envelope."""
    if exc.status_code == 404:
        return JSONResponse(
            status_code=404,
            content={"error": "not_found", "message": "Route not found."},
        )

    message = str(exc.detail) if exc.detail else "HTTP error."
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": "http_error", "message": message},
    )

#includes the API routers for core functionality, beetle-related endpoints, and map-related endpoints into the FastAPI application, making their routes available for handling incoming requests.
app.include_router(core_router)
app.include_router(beetle_router)
app.include_router(beetle_write_router)
app.include_router(map_router)
app.include_router(auth_router)
