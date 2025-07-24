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
        rag_deps.initialize()
        logger.info("RAG dependencies initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize RAG dependencies: {e}")
        raise
    yield
    logger.info("Shutting down NobelLM FastAPI application...")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    settings = get_settings()

    # Comprehensive CORS origins for production reliability
    logger.info("Configuring CORS for production")
    cors_origins = [
        "https://nobellm.com",
        "https://www.nobellm.com", 
        "https://nobellm-web.fly.dev",
        "http://localhost:3000",  # For local development
        "http://localhost:5173",  # For local development
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

    # Add CORS middleware with comprehensive configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["*"]
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

    @app.middleware("http")
    async def add_cors_debug_headers(request: Request, call_next):
        """Add CORS debug headers for troubleshooting."""
        response = await call_next(request)
        
        # Add debug headers
        origin = request.headers.get("origin")
        response.headers["X-CORS-Origin"] = origin or "none"
        response.headers["X-CORS-Allowed-Origins"] = ", ".join(cors_origins)
        
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

    @app.get("/health")
    async def health_check():
        """Comprehensive health check including Qdrant connectivity."""
        current_settings = get_settings()
        health_status = {
            "status": "healthy",
            "timestamp": time.time(),
            "version": current_settings.app_version,
            "checks": {}
        }
        
        # Check Qdrant connectivity
        try:
            from qdrant_client import QdrantClient
            qdrant_url = current_settings.qdrant_url
            qdrant_api_key = current_settings.qdrant_api_key
            client = QdrantClient(url=qdrant_url, api_key=qdrant_api_key)
            # Test basic connectivity
            client.get_collections()
            health_status["checks"]["qdrant_connectivity"] = "ok"
            # Perform warmup search
            try:
                from rag.query_qdrant import query_qdrant
                warmup_results = query_qdrant(
                    query_text="test",
                    top_k=1,
                    score_threshold=0.0
                )
                health_status["checks"]["qdrant_query"] = "ok"
                health_status["checks"]["qdrant_results"] = len(warmup_results) if warmup_results else 0
            except Exception as e:
                health_status["checks"]["qdrant_query"] = f"error: {str(e)}"
                health_status["status"] = "degraded"
        except Exception as e:
            health_status["checks"]["qdrant_connectivity"] = f"error: {str(e)}"
            health_status["status"] = "unhealthy"
        
        # Check theme embeddings
        try:
            from config.theme_embeddings import ThemeEmbeddings
            theme_embeddings = ThemeEmbeddings("bge-large")
            stats = theme_embeddings.get_embedding_stats()
            health_status["checks"]["theme_embeddings"] = {
                "status": "ok",
                "total_keywords": stats.get("total_keywords", 0),
                "model": stats.get("model_id", "unknown")
            }
        except Exception as e:
            health_status["checks"]["theme_embeddings"] = f"error: {str(e)}"
            health_status["status"] = "degraded"
        
        return health_status

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
