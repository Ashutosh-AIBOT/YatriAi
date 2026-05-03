import json
import redis.asyncio as aioredis
from ..config import settings

_redis = None

async def get_redis():
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(settings.redis_url, decode_responses=True)
    return _redis

async def get_cached(key: str):
    r = await get_redis()
    val = await r.get(key)
    return json.loads(val) if val else None

async def set_cached(key: str, value, ttl: int = 3600):
    r = await get_redis()
    await r.set(key, json.dumps(value), ex=ttl)

async def delete_cached(key: str):
    r = await get_redis()
    await r.delete(key)
