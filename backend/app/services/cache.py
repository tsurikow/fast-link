import redis.asyncio as redis

from backend.app.core.config import settings

# Create a global Redis client instance
redis_client = redis.Redis(
    host=settings.REDIS_HOST,
    port=settings.REDIS_PORT,
    password=settings.REDIS_PASSWORD,
    decode_responses=True
)

async def set_cache(key: str, value: str, expire: int = None) -> bool:
    return await redis_client.set(key, value, ex=expire)

async def get_cache(key: str) -> str:
    return await redis_client.get(key)

async def delete_cache(key: str) -> int:
    return await redis_client.delete(key)

async def flush_cache() -> bool:
    return await redis_client.flushdb()

async def check_collision(code: str) -> bool:
    """
    Check if the generated short code already exists in Redis.
    Returns True if it exists.
    """
    exists = await redis_client.exists(code)
    return exists == 1

async def store_short_code(code: str, url: str, expire: int = None) -> bool:
    """
    Store the mapping of short code to original URL in Redis.
    Optionally set an expiration time (in seconds) for the key.
    """
    return await redis_client.set(code, url, ex=expire)
