from contextlib import asynccontextmanager

from fastapi import FastAPI

from src.core.neo4j_lifespan import neo4j_lifespan
from src.database.graph_schema import install_graph_schema


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Комбинирует lifespan Neo4j и установку схемы
    """
    async with neo4j_lifespan(app):
        await install_graph_schema()
        yield


app = FastAPI(lifespan=lifespan)


@app.get("/health")
async def health():
    return {"status": "ok"}
