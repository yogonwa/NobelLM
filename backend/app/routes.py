"""
API routes for NobelLM FastAPI backend.

This module defines the REST API endpoints for querying the RAG pipeline.
"""

import logging
from typing import Dict, Any, Optional
import time

from utils.audit_logger import start_query_audit, complete_query_audit
from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import JSONResponse, Response
from pydantic import BaseModel, Field

# Use the audited version of answer_query for comprehensive logging
from rag.query_engine_audit import answer_query
from .deps import get_rag_dependencies, get_settings_dep, validate_query
from .config import Settings

logger = logging.getLogger(__name__)

router = APIRouter()


class QueryRequest(BaseModel):
    """Request model for query endpoint."""
    
    query: str = Field(..., min_length=1, max_length=1000, description="The query to process")
    model_id: Optional[str] = Field(None, description="Model ID to use for embeddings")
    top_k: Optional[int] = Field(5, ge=1, le=20, description="Number of chunks to retrieve")
    score_threshold: Optional[float] = Field(0.2, ge=0.0, le=1.0, description="Minimum similarity score")
    filters: Optional[Dict[str, Any]] = Field(None, description="Metadata filters for retrieval")


class QueryResponse(BaseModel):
    """Response model for query endpoint."""
    
    answer: str = Field(..., description="Generated answer")
    sources: list = Field(..., description="Source chunks used")
    model_id: str = Field(..., description="Model ID used")
    query: str = Field(..., description="Original query")
    metadata: Dict[str, Any] = Field(..., description="Additional metadata")
    answer_type: Optional[str] = Field(None, description="Type of answer: 'rag' or 'metadata'")
    metadata_answer: Optional[Dict[str, Any]] = Field(None, description="Structured metadata answer, if available")


class HealthResponse(BaseModel):
    """Response model for health check endpoint."""
    
    status: str = Field(..., description="Service status")
    version: str = Field(..., description="API version")
    model_id: str = Field(..., description="Current model ID")


@router.get("/health", response_model=HealthResponse)
async def health_check(
    rag_deps = Depends(get_rag_dependencies),
    settings: Settings = Depends(get_settings_dep)
) -> HealthResponse:
    """
    Health check endpoint.
    
    Returns:
        Health status and service information
    """
    try:
        # Initialize RAG dependencies if not already done
        rag_deps.initialize()
        
        return HealthResponse(
            status="healthy",
            version=settings.app_version,
            model_id=rag_deps.model_id
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        raise HTTPException(status_code=503, detail="Service unhealthy")


@router.get("/readyz")
async def readiness_check():
    """
    Lightweight readiness check endpoint for frontend warm-up.
    
    This endpoint is designed to be fast and lightweight for warming up
    the backend service when users load the web app.
    """
    start_time = time.time()
    try:
        settings = get_settings_dep()
        duration = time.time() - start_time
        logger.info(f"Readiness check completed in {duration:.3f}s", extra={
            "event": "warmup_backend_success",
            "duration_ms": int(duration * 1000),
            "service": "nobellm-api"
        })
        
        return JSONResponse(
            content={
                "status": "ready",
                "timestamp": time.time(),
                "service": "nobellm-api",
                "version": settings.app_version,
            },
            media_type="application/json"
        )
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"Readiness check failed after {duration:.3f}s: {e}", extra={
            "event": "warmup_backend_failed",
            "duration_ms": int(duration * 1000),
            "error": str(e),
            "service": "nobellm-api"
        })
        raise HTTPException(status_code=503, detail="Service unavailable")


@router.get("/modal/warmup")
async def modal_warmup():
    """
    Lightweight Modal warm-up endpoint.
    
    This endpoint triggers a simple embedding call to warm up the Modal
    service when users load the web app. Returns 204 for successful no-op.
    """
    start_time = time.time()
    try:
        # Import Modal service
        from rag.modal_embedding_service import ModalEmbeddingService
        
        # Create service instance and do a lightweight warm-up
        modal_service = ModalEmbeddingService()
        
        # Simple warm-up call - embed a short text
        warmup_text = "hello"
        embedding = await modal_service.embed_text(warmup_text)
        
        if embedding and len(embedding) > 0:
            duration = time.time() - start_time
            logger.info(f"Modal service warmed successfully for warm-up probe in {duration:.3f}s", extra={
                "event": "warmup_modal_success",
                "duration_ms": int(duration * 1000),
                "embedding_size": len(embedding),
                "service": "modal-embedding"
            })
            # Return 204 No Content for successful no-op
            return Response(status_code=204)
        else:
            duration = time.time() - start_time
            logger.error(f"Modal warm-up failed after {duration:.3f}s: empty embedding returned", extra={
                "event": "warmup_modal_failed",
                "duration_ms": int(duration * 1000),
                "error": "empty_embedding",
                "service": "modal-embedding"
            })
            raise HTTPException(status_code=503, detail="Modal service warm-up failed")
            
    except ImportError as e:
        duration = time.time() - start_time
        logger.error(f"Modal import failed during warm-up after {duration:.3f}s: {e}", extra={
            "event": "warmup_modal_failed",
            "duration_ms": int(duration * 1000),
            "error": "import_error",
            "service": "modal-embedding"
        })
        raise HTTPException(status_code=503, detail="Modal service unavailable")
    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"Modal warm-up failed after {duration:.3f}s: {e}", extra={
            "event": "warmup_modal_failed",
            "duration_ms": int(duration * 1000),
            "error": str(e),
            "service": "modal-embedding"
        })
        raise HTTPException(status_code=503, detail="Modal service unavailable")


@router.post("/query", response_model=QueryResponse)
async def process_query(
    request: QueryRequest,
    rag_deps = Depends(get_rag_dependencies),
    settings: Settings = Depends(get_settings_dep)
) -> QueryResponse:
    """
    Process a query using the RAG pipeline.
    
    Args:
        request: Query request with parameters
        rag_deps: RAG dependencies
        settings: Application settings
    
    Returns:
        Query response with answer and sources
    
    Raises:
        HTTPException: If query processing fails
    """
    try:
        # Validate query
        query = validate_query(request.query, settings)
        
        # Initialize RAG dependencies with specified model
        model_id = request.model_id or settings.default_model
        rag_deps.initialize(model_id)
        
        logger.info(f"Processing query: '{query[:50]}...' with model: {model_id}")
        
        # Process query using RAG pipeline
        result = answer_query(
            query,
            model_id,
            request.score_threshold or settings.default_score_threshold,
            None,  # min_return (use default)
            request.top_k or settings.default_top_k  # max_return
        )
        
        # Extract sources from result
        sources = []
        if isinstance(result, dict):
            sources = result.get("sources", [])
        elif hasattr(result, 'sources') and result.sources:
            sources = result.sources
        elif hasattr(result, 'chunks') and result.chunks:
            sources = result.chunks
        
        # Extract answer from result
        if isinstance(result, dict):
            answer = result.get("answer", "")
        elif hasattr(result, 'answer') and result.answer:
            answer = result.answer
        elif hasattr(result, 'response') and result.response:
            answer = result.response
        elif isinstance(result, str):
            answer = result
        else:
            answer = str(result)
        
        logger.info(f"Query processed successfully. Answer length: {len(answer)}")
        
        return QueryResponse(
            answer=answer,
            sources=sources,
            model_id=model_id,
            query=query,
            metadata={
                "top_k": request.top_k or settings.default_top_k,
                "score_threshold": request.score_threshold or settings.default_score_threshold,
                "filters_applied": bool(request.filters)
            },
            answer_type=result.get("answer_type"),
            metadata_answer=result.get("metadata_answer")
        )
        
    except ValueError as e:
        logger.warning(f"Invalid query request: {e}")
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Query processing failed: {e}")
        raise HTTPException(status_code=500, detail="Internal server error")


@router.get("/models")
async def list_models() -> Dict[str, Any]:
    """
    List available models.
    
    Returns:
        Available model configurations
    """
    try:
        from rag.model_config import MODEL_CONFIGS
        return {
            "models": list(MODEL_CONFIGS.keys()),
            "default_model": "bge-large"
        }
    except Exception as e:
        logger.error(f"Failed to list models: {e}")
        raise HTTPException(status_code=500, detail="Failed to retrieve model list") 