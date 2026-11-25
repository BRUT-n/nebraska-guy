import json
from logging import getLogger
from typing import Any

from redis.asyncio import RedisError

from src.core.redis_client import get_redis_client

logger = getLogger(__name__)


async def cache_get(key: str) -> dict | None:
    """
    Достает JSON из кеша, или None если проблемы с кешом.
    """
    try:
        client = await get_redis_client()
        raw = await client.get(key)
    except RedisError as exc:
        logger.warning("Falied in cache_get for key %s: %s", key, exc)
        return None

    if raw is None:
        return None

    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        logger.warning("Can not decode JSON in cache_get for key %s: %s", key, exc)
        return None


async def cache_set(key: str, value: Any, ttl_seconds: int) -> None:
    """
    Сохраняет JSON с TTL. Ошибки Redis логируются как warning.
    """
    try:
        client = await get_redis_client()
        payload = json.dumps(value, default=str)
        await client.set(key, payload, ttl_seconds)
    except RedisError as exc:
        logger.warning("Can not set in cache_set for key %s: %s", key, exc)
    except TypeError as exc:
        logger.warning("Can not encode %s to JSON for: %s", key, exc)


async def cache_delete(key: str) -> None:
    """
    Удаляет запись в кеше по ключу.
    """
    try:
        client = await get_redis_client()
        await client.delete(key)
    except RedisError as exc:
        logger.warning("Can not delete raw in cache_delete for %s: %s", key, exc)
