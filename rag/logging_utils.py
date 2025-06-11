"""
Centralized logging configuration for NobelLM RAG pipeline.

This module provides a single source of truth for logging configuration
and helper functions for consistent logging across the RAG pipeline.
"""
import logging
import uuid
import contextvars
from typing import Optional, Dict, Any, List
from contextlib import contextmanager
import json
from datetime import datetime

# Context variables for request tracking
query_id = contextvars.ContextVar("query_id", default=None)
model_id = contextvars.ContextVar("model_id", default=None)

def setup_logging(level: int = logging.INFO) -> None:
    """
    Configure logging for the entire RAG pipeline.
    Should be called once at application startup.
    
    Args:
        level: Logging level (default: INFO)
    """
    if logging.getLogger().handlers:
        return  # Already configured
        
    logging.basicConfig(
        level=level,
        format="%(asctime)s %(levelname)-8s %(name)s:%(lineno)d [%(message)s]",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

def get_module_logger(name: str) -> logging.Logger:
    """
    Get a configured logger for a module.
    Ensures consistent logger setup across the codebase.
    
    Args:
        name: Name of the module (usually __name__)
        
    Returns:
        Configured logger instance
    """
    return logging.getLogger(name)

def format_log_message(
    component: str,
    message: str,
    extra: Optional[Dict[str, Any]] = None
) -> str:
    """
    Format a log message with component and context.
    
    Args:
        component: Component name (e.g., "QueryEngine")
        message: Log message
        extra: Additional context to include
        
    Returns:
        Formatted log message
    """
    # Get current context
    ctx = {
        "query_id": query_id.get(),
        "model_id": model_id.get()
    }
    
    # Add any extra context
    if extra:
        ctx.update(extra)
    
    # Convert numpy types to JSON-serializable types
    def convert_numpy_types(obj):
        if hasattr(obj, 'dtype'):  # numpy array or scalar
            return str(obj.dtype)
        elif hasattr(obj, '__class__') and 'numpy' in str(obj.__class__):
            return str(obj)
        elif isinstance(obj, dict):
            return {k: convert_numpy_types(v) for k, v in obj.items()}
        elif isinstance(obj, (list, tuple)):
            return [convert_numpy_types(item) for item in obj]
        else:
            return obj
    
    # Convert context to JSON-serializable format
    serializable_ctx = convert_numpy_types(ctx)
    
    # Format as JSON for structured logging
    return f"[{component}] {message} | {json.dumps(serializable_ctx)}"

def log_with_context(
    logger: logging.Logger,
    level: int,
    component: str,
    message: str,
    extra: Optional[Dict[str, Any]] = None
) -> None:
    """
    Log a message with component and context.
    
    Args:
        logger: Logger instance
        level: Logging level
        component: Component name
        message: Log message
        extra: Additional context
    """
    formatted = format_log_message(component, message, extra)
    logger.log(level, formatted)

def generate_query_id() -> str:
    """Generate a unique query ID."""
    return str(uuid.uuid4())

class QueryContext:
    """
    Context manager for query-scoped logging.
    
    This class manages context variables for request tracking,
    ensuring they are properly set and reset around query processing.
    """
    
    def __init__(self, model_id_value: Optional[str] = None):
        """
        Initialize the context manager.
        
        Args:
            model_id_value: Optional model ID to set in context
        """
        self._tokens = []
        self._model_id_value = model_id_value
    
    def __enter__(self) -> "QueryContext":
        """Set up context variables for the query."""
        # Generate a unique query ID
        query_id_value = str(uuid.uuid4())
        
        # Set context variables
        self._tokens = [
            query_id.set(query_id_value)
        ]
        
        if self._model_id_value is not None:
            self._tokens.append(model_id.set(self._model_id_value))
        
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Reset context variables."""
        # Reset each context variable to its default
        for token in self._tokens:
            if token.var == query_id:
                query_id.reset(token)
            elif token.var == model_id:
                model_id.reset(token)
            else:
                # For any other context vars, just reset to None
                token.var.set(None) 