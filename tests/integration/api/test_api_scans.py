import pytest
from fastapi import status
from httpx import AsyncClient


@pytest.mark.asyncio(loop_scope="session")
async def test_create_scan_success(client: AsyncClient):
    """
    Проверка успешного создания скана.
    """
    payload = {"root_package": "Package", "root_ecosystem": "pypi"}
    response = await client.post("/scans", json=payload)

    assert response.status_code == status.HTTP_201_CREATED

    data = response.json()
    assert data["scan_id"] == 1
    assert data["root_package"] == "package"
    assert data["status"] == "pending"
    assert data["completed_at"] is None


@pytest.mark.asyncio(loop_scope="session")
async def test_get_scan_success(client: AsyncClient):
    """
    Проверяет успешный вывод скана из БД по схеме.
    """
    payload = {"root_package": "Package", "root_ecosystem": "pypi"}
    existing_scan = await client.post("/scans", json=payload)
    existing_scan = existing_scan.json()

    response = await client.get(f"/scans/{existing_scan['scan_id']}")

    assert response.status_code == status.HTTP_200_OK

    data = response.json()
    assert data["root_package"] == "package"
    assert data["scan_id"] == existing_scan["scan_id"]


@pytest.mark.asyncio(loop_scope="session")
async def test_get_scan_not_found(client: AsyncClient):
    """
    Проверяет ошибку несуществующего скана.
    """
    response = await client.get("/scans/999")

    assert response.status_code == status.HTTP_404_NOT_FOUND


@pytest.mark.asyncio(loop_scope="session")
async def test_get_list_scans_success(client: AsyncClient):
    """
    Проверяет отображание листа сканов с пагинацией.
    """
    for i in range(15):
        await client.post("/scans", json={"root_package": f"pkg-{i}"})

    page1 = await client.get("/scans?limit=10&offset=0")
    assert page1.status_code == status.HTTP_200_OK
    assert len(page1.json()) == 10

    page2 = await client.get("/scans?limit=10&offset=10")
    assert page2.status_code == status.HTTP_200_OK
    assert len(page2.json()) == 5
