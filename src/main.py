from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from neomodel import adb, get_config

from src.api.v1.scans import router as scans_router
from src.core.redis_client import close_redis_client, get_redis_client
from src.database.graph_schema import install_graph_schema
from src.settings import build_neo4j_url


@asynccontextmanager
async def neo4j_lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Инициализирует подключение к Neo4j при старте, закрывает при остановке."""
    config = get_config()
    config.database_url = build_neo4j_url()

    await adb.set_connection(config.database_url)
    yield
    await adb.close_connection()


@asynccontextmanager
async def redis_lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """
    Инициализирует клиент Redis при старте и закрывает при остановке
    """
    redis = await get_redis_client()
    await redis.ping()
    yield
    await close_redis_client()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Комбинирует lifespan Neo4j и установку схемы.
    """
    async with neo4j_lifespan(app), redis_lifespan(app):
        await install_graph_schema()
        yield


app = FastAPI(lifespan=lifespan)
app.include_router(scans_router)


@app.get("/health")
async def health():
    return {"status": "ok"}
