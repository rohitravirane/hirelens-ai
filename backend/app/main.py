"""
HireLens AI - Main FastAPI application
"""
from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import structlog

from app.core.config import settings
from app.core.database import init_db
from app.core.logging_config import configure_logging
from app.core.middleware import (
    CorrelationIDMiddleware,
    LoggingMiddleware,
    ExceptionHandlerMiddleware,
)
from app.core.exceptions import HireLensException
from app.auth.router import router as auth_router
from app.resumes.router import router as resumes_router
from app.jobs.router import router as jobs_router
from app.candidates.router import router as candidates_router
from app.matching.router import router as matching_router

# Configure logging
configure_logging()
logger = structlog.get_logger()

# Create FastAPI app
app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="Production-Grade AI-Powered Hiring Intelligence Platform",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# Add middleware
app.add_middleware(CorrelationIDMiddleware)
app.add_middleware(LoggingMiddleware)
app.add_middleware(ExceptionHandlerMiddleware)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Global exception handler
@app.exception_handler(HireLensException)
async def hirelens_exception_handler(request: Request, exc: HireLensException):
    """Handle HireLens exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "message": exc.message,
                "details": exc.details,
                "type": exc.__class__.__name__,
            }
        },
    )


# Health check
@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {
        "status": "healthy",
        "service": settings.APP_NAME,
        "version": settings.APP_VERSION,
    }


# Root endpoint
@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs": "/api/docs",
    }


# Include routers
app.include_router(auth_router)
app.include_router(resumes_router)
app.include_router(jobs_router)
app.include_router(candidates_router)
app.include_router(matching_router)


# Startup event
@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    logger.info("application_starting", version=settings.APP_VERSION)
    
    # Initialize database
    try:
        init_db()
        logger.info("database_initialized")
    except Exception as e:
        logger.error("database_init_failed", error=str(e))


# Shutdown event
@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("application_shutting_down")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        reload=settings.DEBUG,
    )

