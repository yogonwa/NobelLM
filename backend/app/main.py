"""
Main FastAPI application for NobelLM backend.

This module initializes the FastAPI application with middleware,
CORS configuration, and route registration.
"""

import logging
import os
import json
import time
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse

from app.config import get_settings, Settings
from app.routes import router
from app.deps import get_rag_dependencies

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

try:
    import rag  # noqa: F401
except ModuleNotFoundError:
    import sys
    print("\n[ERROR] Could not import 'rag'. Please run the backend from the NobelLM project root or set PYTHONPATH to the project root.\n", file=sys.stderr)
    sys.exit(1)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info("Starting NobelLM FastAPI application...")
    try:
        rag_deps = get_rag_dependencies()
        # rag_deps.initialize()
        logger.info("RAG dependencies initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize RAG dependencies: {e}")
        raise
    yield
    logger.info("Shutting down NobelLM FastAPI application...")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    settings = get_settings()

    # Hardcoded CORS origins for production reliability
    logger.info("Using hardcoded CORS origins for production")
    cors_origins = [
        "https://nobellm.com",
        "https://www.nobellm.com",
        "https://nobellm-web.fly.dev"
    ]

    logger.info(f"CORS origins configured: {cors_origins}")

    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Nobel Laureate Speech Explorer API - RAG-powered query interface",
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        lifespan=lifespan
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"]
    )

    if not settings.debug:
        trusted_hosts = [
            "nobellm.com",
            "www.nobellm.com",
            "nobellm-web.fly.dev",
            "*.fly.dev"
        ]
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=trusted_hosts
        )
        logger.info(f"Trusted hosts configured: {trusted_hosts}")
    else:
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["*"]
        )
        logger.info("Development mode: allowing all hosts")

    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        response.headers["X-Process-Time"] = str(time.time() - start_time)
        return response

    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {exc}")
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )

    app.include_router(router, prefix="/api", tags=["api"])

    @app.get("/")
    async def root():
        return {
            "name": settings.app_name,
            "version": settings.app_version,
            "status": "running",
            "docs": "/docs" if settings.debug else "Documentation disabled in production"
        }

    @app.get("/debug/cors")
    def debug_cors():
        return {"cors_origins": cors_origins}

    return app


app = create_app()


if __name__ == "__main__":
    import uvicorn
    settings = get_settings()
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )
