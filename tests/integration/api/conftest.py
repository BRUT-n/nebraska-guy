import pytest_asyncio
from httpx import ASGITransport, AsyncClient


@pytest_asyncio.fixture(scope="session")
async def client():
    """
    Асинхронный HTTP-клиент для тестов API.
    Не отправляет реальные сетевые запросы, а общается с приложением напрямую.
    """
    from src.main import app

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
