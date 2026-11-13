import redis.asyncio as redis

from app.core.config import settings

redis_client = redis.from_url(
    getattr(settings, "REDIS_URL", "redis://localhost:6379/0"),
    decode_responses=True,
    socket_connect_timeout=3,
    socket_timeout=3,
)

async def check_redis():
    return await redis_client.ping()

async def close_redis():
    await redis_client.aclose()