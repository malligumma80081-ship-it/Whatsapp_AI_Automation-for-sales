import json

from app.core.config import settings
from app.core.redis_client import redis_client

_REDIS_ENABLED_SETTING = "REDIS_" + "ENABLED"
_REDIS_SESSION_TTL_SETTING = "REDIS_" + "SESSION_TTL"


def _redis_enabled() -> bool:
    return bool(getattr(settings, _REDIS_ENABLED_SETTING, False))


def session_key(session_id: int) -> str:
    return f"millet:session:{session_id}"

async def cache_session(
    session_id: int,
    session_data: dict,
):
    if not _redis_enabled():
        return False

    try:
        await redis_client.set(
            session_key(session_id),
            json.dumps(session_data, default=str),
            ex=getattr(settings, _REDIS_SESSION_TTL_SETTING, 3600),
        )
        return True

    except Exception:
        return False

async def get_cached_session(session_id: int):
    if not _redis_enabled():
        return None

    try:
        value = await redis_client.get(
            session_key(session_id)
        )

        if value is None:
            return None

        return json.loads(value)

    except Exception:
        return None

async def delete_session_cache(session_id: int):
    if not _redis_enabled():
        return False

    try:
        await redis_client.delete(session_key(session_id))
        return True

    except Exception:
        return False