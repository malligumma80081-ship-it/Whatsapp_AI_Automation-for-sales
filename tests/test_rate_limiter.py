import asyncio
from types import SimpleNamespace

from app.core import rate_limiter


class DummyRequest:
    def __init__(self):
        self.client = SimpleNamespace(host="127.0.0.1")
        self.method = "POST"
        self.url = SimpleNamespace(path="/api/v1/auth/login")


def test_rate_limiter_skips_when_disabled(monkeypatch):
    monkeypatch.setattr(rate_limiter.settings, "RATE_LIMIT_ENABLED", False)
    monkeypatch.setattr(rate_limiter.settings, "REDIS_ENABLED", False)

    dependency = rate_limiter.rate_limit(5, 60)
    result = asyncio.run(dependency(DummyRequest()))

    assert result is None


def test_rate_limiter_allows_when_redis_unavailable(monkeypatch):
    async def raise_error(*args, **kwargs):
        raise RuntimeError("redis down")

    monkeypatch.setattr(rate_limiter.settings, "RATE_LIMIT_ENABLED", True)
    monkeypatch.setattr(rate_limiter.settings, "REDIS_ENABLED", True)
    monkeypatch.setattr(rate_limiter.redis_client, "eval", raise_error)

    dependency = rate_limiter.rate_limit(5, 60)
    result = asyncio.run(dependency(DummyRequest()))

    assert result is None
