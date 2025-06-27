"""
Configuration management for NobelLM FastAPI backend.

Handles environment variable loading, validation, and deployment-safe defaults.
Compatible with Fly.io deployment using string-based env vars.
"""
from pydantic_settings import BaseSettings
from pydantic import validator
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

    # --- RAG Config ---
    default_model: str = "bge-large"
    max_query_length: int = 1000
    default_top_k: int = 5
    default_score_threshold: float = 0.2

    # --- Logging ---
    log_level: str = "INFO"

    # --- CORS ---
    cors_origins: List[str] = []

    @validator("openai_api_key")
    def validate_openai_key(cls, v):
        if not v or not v.startswith("sk-"):
            raise ValueError("Invalid OpenAI API key format")
        return v

    @validator("debug")
    def derive_debug_mode(cls, v):
        return os.environ.get("ENVIRONMENT", "").lower() == "development"

    @validator("cors_origins", pre=True)
    def split_cors_origins(cls, v):
        if isinstance(v, str):
            return [s.strip() for s in v.split(",") if s.strip()]
        return v

    class Config:
        case_sensitive = False
        extra = "ignore"

# Singleton instance
settings = Settings()


def get_settings() -> Settings:
    return settings
