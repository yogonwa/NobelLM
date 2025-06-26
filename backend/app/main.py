"""
Main FastAPI application for NobelLM backend.

This module initializes the FastAPI application with middleware,
CORS configuration, and route registration.
"""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import time

from .config import get_settings, Settings
from .routes import router
from .deps import get_rag_dependencies

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
    # Startup
    logger.info("Starting NobelLM FastAPI application...")
    
    try:
        # Initialize RAG dependencies
        rag_deps = get_rag_dependencies()
        rag_deps.initialize()
        logger.info("RAG dependencies initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize RAG dependencies: {e}")
        raise
    
    yield
    
    # Shutdown
    logger.info("Shutting down NobelLM FastAPI application...")


def create_app() -> FastAPI:
    """Create and configure FastAPI application."""
    settings = get_settings()
    
    app = FastAPI(
        title=settings.app_name,
        version=settings.app_version,
        description="Nobel Laureate Speech Explorer API - RAG-powered query interface",
        docs_url="/docs" if settings.debug else None,
        redoc_url="/redoc" if settings.debug else None,
        lifespan=lifespan
    )
    
    # Log CORS configuration for debugging
    logger.info(f"CORS origins configured: {settings.cors_origins}")
    
    # Add CORS middleware with best practices configuration
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,  # Explicit list of allowed origins
        allow_credentials=True,  # Allow cookies and auth headers
        allow_methods=["GET", "POST", "OPTIONS", "HEAD"],  # Explicit methods
        allow_headers=["*"],  # Allow all headers
        expose_headers=["X-Process-Time"],  # Expose custom headers
        max_age=86400,  # Cache preflight requests for 24 hours
    )
    
    # Add trusted host middleware for production
    if not settings.debug:
        # Production trusted hosts
        trusted_hosts = [
            "nobellm.com",
            "www.nobellm.com", 
            "nobellm-web.fly.dev",
            "*.fly.dev"  # Allow any Fly.io subdomain
        ]
        
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=trusted_hosts
        )
        logger.info(f"Trusted hosts configured: {trusted_hosts}")
    else:
        # Development: allow all hosts
        app.add_middleware(
            TrustedHostMiddleware,
            allowed_hosts=["*"]
        )
        logger.info("Development mode: allowing all hosts")
    
    # Add request timing middleware
    @app.middleware("http")
    async def add_process_time_header(request: Request, call_next):
        start_time = time.time()
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = str(process_time)
        return response
    
    # Add global exception handler
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        logger.error(f"Unhandled exception: {exc}")
        return JSONResponse(
            status_code=500,
            content={"detail": "Internal server error"}
        )
    
    # Include API routes
    app.include_router(router, prefix="/api", tags=["api"])
    
    # Root endpoint
    @app.get("/")
    async def root():
        """Root endpoint with API information."""
        return {
            "name": settings.app_name,
            "version": settings.app_version,
            "status": "running",
            "docs": "/docs" if settings.debug else "Documentation disabled in production"
        }
    
    return app


# Create application instance
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