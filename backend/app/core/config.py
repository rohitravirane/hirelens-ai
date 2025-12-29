"""
Application configuration using Pydantic Settings
"""
from typing import List, Optional
from pydantic_settings import BaseSettings
from pydantic import Field


class Settings(BaseSettings):
    """Application settings loaded from environment variables"""
    
    # Application
    APP_NAME: str = "HireLens AI"
    APP_VERSION: str = "1.0.0"
    ENVIRONMENT: str = "development"
    DEBUG: bool = True
    SECRET_KEY: str = Field(..., min_length=32)
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
    OPENAI_API_KEY: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4-turbo-preview"
    EMBEDDING_MODEL: str = "text-embedding-3-large"
    AI_TEMPERATURE: float = 0.3
    AI_MAX_TOKENS: int = 2000
    
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

