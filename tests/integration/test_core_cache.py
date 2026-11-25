import pytest
from src.core.cache import cache_delete, cache_get, cache_set

KEY = "some_key"
VALUE = {"info": {"author": "nickname", "email": "some@sv.com"}, "role": "owner"}
TTL = 60


@pytest.mark.asyncio(loop_scope="session")
async def test_cache_set_and_get_success():
    """
    Проверяет внесение и получение данных из кеша.
    """
    await cache_set(KEY, VALUE, TTL)
    result = await cache_get(KEY)

    assert result == VALUE


@pytest.mark.asyncio(loop_scope="session")
async def test_cache_delete():
    """
    Проверяет удаление записи в кеше по ключу.
    """
    await cache_set(KEY, VALUE, TTL)
    await cache_delete(KEY)

    assert await cache_get(KEY) is None
