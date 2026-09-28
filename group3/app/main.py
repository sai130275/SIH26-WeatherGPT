"""
main.py
-------
FastAPI application factory for Group 3 – AI & Weather Intelligence.

This module:
  1. Creates and configures the FastAPI app instance.
  2. Registers all API routers.
  3. Adds global exception handlers.

Run with:
    uvicorn app.main:app --reload
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.routes import health, analyze, risk
from app.core.config import settings


def create_app() -> FastAPI:
    """
    Application factory.

    Returns a fully-configured FastAPI instance.  Keeping construction
    inside a factory function makes the app easy to test (each test can
    spin up a fresh instance) and easier to extend later.
    """
    app = FastAPI(
        title=settings.APP_NAME,
        version=settings.APP_VERSION,
        description=(
            "Group 3 micro-service: AI-powered weather intelligence layer. "
            "Provides weather data processing, condition detection, risk/impact "
            "assessment, and LLM-generated advisories for the WeatherGPT platform."
        ),
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
    )

    # ------------------------------------------------------------------ #
    # CORS – allow Group 2 (Node.js) and future clients to call this API  #
    # ------------------------------------------------------------------ #
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],   # tighten in production via env var
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # ------------------------------------------------------------------ #
    # Routers                                                              #
    # ------------------------------------------------------------------ #
    app.include_router(health.router)
    app.include_router(analyze.router)
    app.include_router(risk.router)

    # ------------------------------------------------------------------ #
    # Global exception handler                                             #
    # ------------------------------------------------------------------ #
    @app.exception_handler(Exception)
    async def unhandled_exception_handler(
        request: Request, exc: Exception
    ) -> JSONResponse:
        """Catch-all for unexpected server errors."""
        return JSONResponse(
            status_code=500,
            content={"detail": "An unexpected internal error occurred."},
        )

    return app


# Module-level app instance consumed by uvicorn / pytest.
app = create_app()
