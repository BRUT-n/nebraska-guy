import logging

import redis.asyncio as aioredis
from redis.asyncio import Redis

from src.settings import build_redis_url

logger = logging.getLogger(__name__)

_redis_client: Redis | None = None


async def get_redis_client() -> Redis:
    """
    Возвращает singleton-клиент Redis, создавая его при первом вызове.
    decode_responses=True для возвращения строк, вместо байтов.
    Внутри клиента connection pool для переиспользования соединений.
    """
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(build_redis_url(), decode_responses=True)
    return _redis_client


async def close_redis_client() -> None:
    """
    Закрывает клиент и пул соединений.
    """
    global _redis_client
    if _redis_client is not None:
        await _redis_client.aclose()
        _redis_client = None
