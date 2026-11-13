import logging

from fastapi import Request, HTTPException

from app.core.config import settings
from app.core.redis_client import redis_client

logger = logging.getLogger(__name__)

RATE_LIMIT_SCRIPT = """
local current = redis.call('INCR', KEYS[1])

if current == 1 then
    redis.call('EXPIRE', KEYS[1], ARGV[1])
end

local ttl = redis.call('TTL', KEYS[1])

return {current, ttl}
"""

def rate_limit(
    max_requests: int = 60,
    window_seconds: int = 60,
):
    async def dependency(request: Request):

        if not getattr(settings, "RATE_LIMIT_ENABLED", False):
            return

        if not getattr(settings, "REDIS_ENABLED", False):
            return

        client_ip = (
            request.client.host
            if request.client
            else "unknown"
        )

        key = (
            f"rate:{client_ip}:"
            f"{request.method}:{request.url.path}"
        )

        try:
            count, ttl = await redis_client.eval(
                RATE_LIMIT_SCRIPT,
                1,
                key,
                window_seconds,
            )

        except Exception:
            logger.warning(
                "Redis rate limiter unavailable; allowing request to proceed.",
                exc_info=True,
            )
            return

        if int(count) > max_requests:
            raise HTTPException(
                status_code=429,
                detail="Too many requests. Please try again later.",
                headers={
                    "Retry-After": str(max(int(ttl), 1))
                },
            )

    return dependency