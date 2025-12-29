"""
Custom middleware for request processing
"""
import time
import uuid
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse
import structlog

from app.core.exceptions import HireLensException

logger = structlog.get_logger()


class CorrelationIDMiddleware(BaseHTTPMiddleware):
    """Add correlation ID to requests for tracing"""
    
    async def dispatch(self, request: Request, call_next):
        correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())
        
        # Add to context
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(correlation_id=correlation_id)
        
        response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id
        
        return response


class LoggingMiddleware(BaseHTTPMiddleware):
    """Log all requests and responses"""
    
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()
        correlation_id = structlog.contextvars.get_contextvars().get("correlation_id", "unknown")
        
        logger.info(
            "request_started",
            method=request.method,
            path=request.url.path,
            correlation_id=correlation_id,
        )
        
        try:
            response = await call_next(request)
            process_time = time.time() - start_time
            
            logger.info(
                "request_completed",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                process_time=process_time,
                correlation_id=correlation_id,
            )
            
            response.headers["X-Process-Time"] = str(process_time)
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                "request_failed",
                method=request.method,
                path=request.url.path,
                error=str(e),
                process_time=process_time,
                correlation_id=correlation_id,
            )
            raise


class ExceptionHandlerMiddleware(BaseHTTPMiddleware):
    """Handle exceptions and return proper error responses"""
    
    async def dispatch(self, request: Request, call_next):
        try:
            response = await call_next(request)
            return response
        except HireLensException as e:
            return JSONResponse(
                status_code=e.status_code,
                content={
                    "error": {
                        "message": e.message,
                        "details": e.details,
                        "type": e.__class__.__name__,
                    }
                },
            )
        except Exception as e:
            logger.exception("unhandled_exception", error=str(e))
            return JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "message": "Internal server error",
                        "type": "InternalServerError",
                    }
                },
            )

