import json
import logging
import redis.asyncio as aioredis
from ..config import settings

logger = logging.getLogger(__name__)

_redis = None
_redis_available = True

async def get_redis():
    """Get Redis connection with graceful fallback if Redis is down."""
    global _redis, _redis_available
    if not _redis_available:
        return None
    if _redis is None:
        try:
            _redis = aioredis.from_url(settings.redis_url, decode_responses=True)
            # Test connection
            await _redis.ping()
            logger.info("Redis connected successfully")
        except Exception as e:
            logger.warning(f"Redis unavailable, running without cache: {e}")
            _redis_available = False
            _redis = None
            return None
    return _redis

async def get_cached(key: str):
    """Get cached value. Returns None silently if Redis is down."""
    try:
        r = await get_redis()
        if r is None:
            return None
        val = await r.get(key)
        return json.loads(val) if val else None
    except Exception as e:
        logger.warning(f"Cache read failed for key {key}: {e}")
        return None

async def set_cached(key: str, value, ttl: int = 3600):
    """Set cached value with TTL. Silently skips if Redis is down."""
    try:
        r = await get_redis()
        if r is None:
            return
        await r.set(key, json.dumps(value, default=str), ex=ttl)  # ALWAYS set TTL
    except Exception as e:
        logger.warning(f"Cache write failed for key {key}: {e}")

async def delete_cached(key: str):
    """Delete cached value. Silently skips if Redis is down."""
    try:
        r = await get_redis()
        if r is None:
            return
        await r.delete(key)
    except Exception as e:
        logger.warning(f"Cache delete failed for key {key}: {e}")
