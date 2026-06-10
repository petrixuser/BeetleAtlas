from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from starlette.exceptions import HTTPException as StarletteHTTPException
from Database.Backend.App.config.settings import parse_allowed_origins
from Database.Backend.App.routers import beetle_router, core_router, map_router


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
    if isinstance(exc.detail, dict):
        error = exc.detail.get("error", "http_error")
        message = exc.detail.get("message", "Unknown error.")
    else:
        error = "http_error"
        message = str(exc.detail)
    return JSONResponse(status_code=exc.status_code, content={"error": error, "message": message})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(_: Request, __: RequestValidationError):
    return JSONResponse(
        status_code=422,
        content={"error": "validation_error", "message": "Invalid request parameters."},
    )


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_exception_handler(_: Request, __: SQLAlchemyError):
    return JSONResponse(
        status_code=503,
        content={
            "error": "database_unavailable",
            "message": "Database is currently unavailable. Please try again later.",
        },
    )


@app.exception_handler(StarletteHTTPException)
async def starlette_http_exception_handler(_: Request, exc: StarletteHTTPException):
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


app.include_router(core_router)
app.include_router(beetle_router)
app.include_router(map_router)
