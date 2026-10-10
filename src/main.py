from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from neomodel import adb, get_config

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
async def lifespan(app: FastAPI):
    """
    Комбинирует lifespan Neo4j и установку схемы.
    """
    async with neo4j_lifespan(app):
        await install_graph_schema()
        yield


app = FastAPI(lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "ok"}
