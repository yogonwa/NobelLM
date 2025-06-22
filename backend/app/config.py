"""
Configuration management for NobelLM FastAPI backend.

This module handles environment variables, configuration validation,
and settings for development vs. production environments.
"""

import os
from typing import Optional
from pydantic_settings import BaseSettings
from pydantic import validator


class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # OpenAI Configuration
    openai_api_key: str
    
    # Application Configuration
    app_name: str = "NobelLM API"
    app_version: str = "1.0.0"
    debug: bool = False
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    
    # RAG Configuration
    default_model: str = "bge-large"
    max_query_length: int = 1000
    default_top_k: int = 5
    default_score_threshold: float = 0.2
    
    # Logging Configuration
    log_level: str = "INFO"
    
    # CORS Configuration
    cors_origins: list = ["http://localhost:3000", "http://localhost:5173"]
    
    @validator("openai_api_key")
    def validate_openai_key(cls, v):
        """Validate OpenAI API key format."""
        if not v or not v.startswith("sk-"):
            raise ValueError("Invalid OpenAI API key format")
        return v
    
    @validator("debug")
    def validate_debug(cls, v, values):
        """Set debug mode based on environment."""
        if "ENVIRONMENT" in os.environ:
            return os.environ["ENVIRONMENT"] == "development"
        return v
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra environment variables


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings."""
    return settings 