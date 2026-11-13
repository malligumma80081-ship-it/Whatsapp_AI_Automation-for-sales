import json
from typing import Any

from app.core.config import settings
from app.core.redis_client import redis_client

async def get_cache(key: str):
    if not getattr(settings, "REDIS_ENABLED", False):
        return None

    try:
        value = await redis_client.get(key)

        if value is None:
            return None

        return json.loads(value)

    except Exception:
        # Cache failure should not stop the business application.
        return None

async def set_cache(
    key: str,
    value: Any,
    ttl: int | None = None,
):
    if not getattr(settings, "REDIS_ENABLED", False):
        return False

    try:
        await redis_client.set(
            key,
            json.dumps(value, default=str),
            ex=ttl if ttl is not None else getattr(settings, "REDIS_CACHE_TTL", 300),
        )
        return True

    except Exception:
        return False

async def delete_cache(key: str):
    if not getattr(settings, "REDIS_ENABLED", False):
        return False

    try:
        await redis_client.delete(key)
        return True

    except Exception:
        return False

async def delete_cache_pattern(pattern: str):
    """Delete matching cache keys safely using SCAN."""
    if not getattr(settings, "REDIS_ENABLED", False):
        return 0

    try:
        keys = []

        async for key in redis_client.scan_iter(match=pattern):
            keys.append(key)

        if keys:
            return await redis_client.delete(*keys)

        return 0

    except Exception:
        return 0