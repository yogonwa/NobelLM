"""
API routes for NobelLM FastAPI backend.

This module defines the REST API endpoints for querying the RAG pipeline.
"""

import logging
from typing import Dict, Any, Optional

from utils.audit_logger import start_query_audit, complete_query_audit
from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field

from rag.query_engine import answer_query
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