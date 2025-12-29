"""
Redis client for caching and session management
"""
import redis
from typing import Optional, Any
import json
import structlog
from app.core.config import settings

logger = structlog.get_logger()

# Create Redis connection pool
redis_client = redis.from_url(
    settings.REDIS_URL,
    encoding="utf-8",
    decode_responses=True,
    socket_connect_timeout=5,
    socket_timeout=5,
    retry_on_timeout=True,
    health_check_interval=30,
)


def get_cache(key: str) -> Optional[Any]:
    """Get value from cache"""
    try:
        value = redis_client.get(key)
        if value:
            return json.loads(value)
        return None
    except Exception as e:
        logger.error("cache_get_error", key=key, error=str(e))
        return None


def set_cache(key: str, value: Any, ttl: Optional[int] = None) -> bool:
    """Set value in cache with optional TTL"""
    try:
        ttl = ttl or settings.REDIS_CACHE_TTL
        serialized = json.dumps(value, default=str)
        return redis_client.setex(key, ttl, serialized)
    except Exception as e:
        logger.error("cache_set_error", key=key, error=str(e))
        return False


def delete_cache(key: str) -> bool:
    """Delete key from cache"""
    try:
        return bool(redis_client.delete(key))
    except Exception as e:
        logger.error("cache_delete_error", key=key, error=str(e))
        return False


def get_cache_key(prefix: str, *args) -> str:
    """Generate cache key from prefix and arguments"""
    return f"{prefix}:{':'.join(str(arg) for arg in args)}"


def invalidate_pattern(pattern: str) -> int:
    """Invalidate all keys matching pattern"""
    try:
        keys = redis_client.keys(pattern)
        if keys:
            return redis_client.delete(*keys)
        return 0
    except Exception as e:
        logger.error("cache_invalidate_error", pattern=pattern, error=str(e))
        return 0

