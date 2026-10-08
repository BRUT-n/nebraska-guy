from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from neomodel import adb, get_config

from src.core.neo4j_connection import build_neo4j_url


@asynccontextmanager
async def neo4j_lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Инициализирует подключение к Neo4j при старте, закрывает при остановке."""
    config = get_config()
    config.database_url = build_neo4j_url()

    await adb.set_connection(config.database_url)
    yield
    await adb.close_connection()
