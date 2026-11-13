import uuid

import pytest

from app.services.cache_service import (
    get_cache,
    set_cache,
    delete_cache,
)


@pytest.fixture
def anyio_backend():
    return "asyncio"


@pytest.mark.anyio
async def test_cache_set_and_get():
    key = f"test:millet:product:{uuid.uuid4().hex}"
    try:
        await set_cache(
            key,
            {"name": "Ragi Milk", "price": "45"},
            ttl=60,
        )
        result = await get_cache(key)

        assert result is not None
        assert result["name"] == "Ragi Milk"
        assert result["price"] == "45"
    finally:
        await delete_cache(key)


@pytest.mark.anyio
async def test_cache_missing_key():
    key = f"test:missing:{uuid.uuid4().hex}"
    assert await get_cache(key) is None