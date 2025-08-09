import redis.asyncio as redis
from app.core.config import settings

_redis_client_instance = None

async def get_redis_client_instance() -> redis.Redis:
    global _redis_client_instance
    if _redis_client_instance is None:
        _redis_client_instance = redis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis_client_instance

async def close_redis_client_instance():
    global _redis_client_instance
    if _redis_client_instance:
        await _redis_client_instance.close()
        _redis_client_instance = None