"""
Configuration management for NobelLM FastAPI backend.

Handles environment variable loading, validation, and deployment-safe defaults.
Compatible with Fly.io deployment using string-based env vars.
"""
from pydantic_settings import BaseSettings
from pydantic import field_validator, Field
from typing import List
import os

class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    # --- OpenAI ---
    openai_api_key: str

    # --- App Info ---
    app_name: str = "NobelLM API"
    app_version: str = "1.0.0"
    debug: bool = False

    # --- Server ---
    host: str = "0.0.0.0"
    port: int = 8000

    # --- Environment ---
    environment: str = "development"  # development, production

    # --- RAG Config ---
    default_model: str = "bge-large"
    max_query_length: int = 1000
    default_top_k: int = 5
    default_score_threshold: float = 0.2

    # --- Weaviate ---
    use_weaviate: bool = True
    weaviate_url: str = "https://a0dq8xtrtkw6lovkllxw.c0.us-east1.gcp.weaviate.cloud"
    weaviate_api_key: str = ""

    # --- Modal Embedding Service ---
    modal_app_name: str = "nobel-embedder"
    use_modal_embedding: bool = True

    # --- CORS ---
    cors_origins: str = ""
    
    # --- Logging ---
    log_level: str = "DEBUG"
    
    # --- Tokenizers ---
    tokenizers_parallelism: str = "false"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.environment.lower() == "production"
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Parse CORS origins from comma-separated string or JSON array."""
        if not self.cors_origins:
            return []
        
        # Try to parse as JSON array first
        try:
            import json
            origins = json.loads(self.cors_origins)
            if isinstance(origins, list):
                return [str(origin).strip() for origin in origins if origin]
        except (json.JSONDecodeError, TypeError):
            pass
        
        # Fall back to comma-separated string
        origins = [origin.strip() for origin in self.cors_origins.split(",") if origin.strip()]
        return origins

    @field_validator('weaviate_url')
    @classmethod
    def validate_weaviate_url(cls, v: str) -> str:
        """Validate Weaviate URL format."""
        if not v:
            return v
        if not v.startswith(('http://', 'https://')):
            raise ValueError('Weaviate URL must start with http:// or https://')
        return v

    @field_validator('default_score_threshold')
    @classmethod
    def validate_score_threshold(cls, v: float) -> float:
        """Validate score threshold is between 0 and 1."""
        if not 0 <= v <= 1:
            raise ValueError('Score threshold must be between 0 and 1')
        return v

    @field_validator('default_top_k')
    @classmethod
    def validate_top_k(cls, v: int) -> int:
        """Validate top_k is positive."""
        if v <= 0:
            raise ValueError('top_k must be positive')
        return v

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

# Create settings instance
settings = Settings()


def get_settings() -> Settings:
    return settings
