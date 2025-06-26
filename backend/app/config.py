"""
Configuration management for NobelLM FastAPI backend.

This module handles environment variables, configuration validation,
and settings for development vs. production environments.
"""

import os
import json
from typing import Optional, List
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
    
    # CORS Configuration - Environment-specific origins
    cors_origins: List[str] = []
    
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
    
    @validator("cors_origins")
    def validate_cors_origins(cls, v):
        """Validate CORS origins are valid URLs."""
        for origin in v:
            if not origin.startswith(("http://", "https://")):
                raise ValueError(f"Invalid CORS origin: {origin}")
        return v
    
    @validator("cors_origins", pre=True)
    def parse_cors_origins(cls, v):
        """
        Parse CORS origins from environment variable with environment-specific defaults.
        
        Environment variable should be a JSON array string:
        CORS_ORIGINS='["https://nobellm.com","https://www.nobellm.com"]'
        
        Or comma-separated:
        CORS_ORIGINS=https://nobellm.com,https://www.nobellm.com
        """
        # If explicitly provided via environment variable, use that
        if isinstance(v, str):
            try:
                # Try to parse as JSON array
                parsed = json.loads(v)
                if isinstance(parsed, list):
                    return parsed
                else:
                    raise ValueError("CORS_ORIGINS must be a JSON array")
            except json.JSONDecodeError:
                # Fallback: try comma-separated string
                return [origin.strip() for origin in v.split(",") if origin.strip()]
        elif isinstance(v, list):
            return v
        
        # Environment-specific defaults
        environment = os.environ.get("ENVIRONMENT", "development")
        print(f"DEBUG: Environment detected as: {environment}")
        
        if environment == "production":
            cors_origins = [
                "https://nobellm.com",
                "https://www.nobellm.com",
                "https://nobellm-web.fly.dev"  # Fly.io default domain
            ]
        else:
            # Development/local environment
            cors_origins = [
                "http://localhost:3000",
                "http://localhost:5173",
                "http://localhost:8080",  # Common dev server port
                "http://127.0.0.1:3000",
                "http://127.0.0.1:5173"
            ]
        
        print(f"DEBUG: CORS origins set to: {cors_origins}")
        return cors_origins
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra environment variables


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get application settings."""
    return settings 