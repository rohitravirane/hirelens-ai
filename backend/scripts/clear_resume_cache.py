"""
Clear resume parsing cache to force reprocessing
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.redis_client import redis_client
import structlog

logger = structlog.get_logger()

def clear_resume_cache():
    """Clear all resume parsing cache"""
    try:
        # Get all cache keys
        pattern = "cache:ai_parse:*"
        keys = []
        for key in redis_client.scan_iter(match=pattern):
            keys.append(key)
        
        if keys:
            deleted = redis_client.delete(*keys)
            logger.info("cache_cleared", keys_deleted=deleted, total_keys=len(keys))
            print(f"✅ Cleared {deleted} cache keys")
        else:
            logger.info("no_cache_keys_found")
            print("ℹ️  No cache keys found")
    except Exception as e:
        logger.error("cache_clear_failed", error=str(e))
        print(f"❌ Error clearing cache: {e}")

if __name__ == "__main__":
    clear_resume_cache()


