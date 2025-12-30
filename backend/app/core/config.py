"""
Application configuration using Pydantic Settings
"""
from typing import List, Optional, Dict
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    APP_NAME: str = "HireLens AI"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = Field(default="change-this-in-production-min-32-characters-required", min_length=32)
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    
    # Database
    DATABASE_URL: str
    DATABASE_POOL_SIZE: int = 10
    DATABASE_MAX_OVERFLOW: int = 20
    
    # Redis
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_CACHE_TTL: int = 3600
    REDIS_SESSION_TTL: int = 1800
    
    # AI/LLM Configuration
    # Provider: "openai", "huggingface", or "auto" (auto uses HuggingFace if no OpenAI key)
    AI_PROVIDER: str = "auto"
    
    # OpenAI Configuration (Optional)
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    EMBEDDING_MODEL: str = "text-embedding-3-large"
    AI_TEMPERATURE: float = 0.3
    AI_MAX_TOKENS: int = 2000
    
    # Hugging Face Configuration (Local Models - No API Keys Needed)
    HUGGINGFACE_MODEL: str = "microsoft/DialoGPT-medium"  # For text generation
    HUGGINGFACE_EMBEDDING_MODEL: str = "sentence-transformers/all-MiniLM-L6-v2"  # For embeddings
    HUGGINGFACE_LLM_MODEL: str = "mistralai/Mistral-7B-Instruct-v0.1"  # For explanations (smaller: "TinyLlama/TinyLlama-1.1B-Chat-v1.0")
    # Resume Parser Models (auto-downloaded, no API keys needed)
    # Best Quality: "mistralai/Mistral-7B-Instruct-v0.1" (default, production-ready with quantization)
    # Fast: "TinyLlama/TinyLlama-1.1B-Chat-v1.0" (CPU), "microsoft/phi-2" (GPU/CPU)
    HUGGINGFACE_PARSER_MODEL: str = "mistralai/Mistral-7B-Instruct-v0.1"  # Best quality for production
    USE_GPU: bool = False  # Set to True if GPU available (recommended for Mistral)
    MODEL_DEVICE: str = "cpu"  # "cpu" or "cuda"
    # Production optimizations
    USE_QUANTIZATION: bool = True  # Use 8-bit quantization to reduce memory (recommended for production)
    MODEL_MAX_MEMORY: Optional[Dict[str, str]] = None  # Memory limits per device, e.g. {"0": "10GiB", "cpu": "20GiB"}
    
    # Alternative AI Providers
    ANTHROPIC_API_KEY: Optional[str] = None
    COHERE_API_KEY: Optional[str] = None
    
    # File Upload
    MAX_UPLOAD_SIZE_MB: int = 10
    ALLOWED_FILE_EXTENSIONS: List[str] = ["pdf", "docx", "doc"]
    UPLOAD_DIR: str = "./uploads"
    
    # Async Tasks
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    
    # CORS
    CORS_ORIGINS: List[str] = ["http://localhost:3000", "http://localhost:3001"]
    CORS_ALLOW_CREDENTIALS: bool = True
    
    # Observability
    LOG_LEVEL: str = "INFO"
    SENTRY_DSN: Optional[str] = None
    ENABLE_METRICS: bool = True
    
    # Rate Limiting
    RATE_LIMIT_PER_MINUTE: int = 60
    RATE_LIMIT_PER_HOUR: int = 1000
    
    # Email (optional)
    SMTP_HOST: Optional[str] = None
    SMTP_PORT: int = 587
    SMTP_USER: Optional[str] = None
    SMTP_PASSWORD: Optional[str] = None
    SMTP_FROM_EMAIL: str = "noreply@hirelens.ai"
    
    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()

