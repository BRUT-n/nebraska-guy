from datetime import datetime

from src.database.crud.scans import (
    count_scans,
    create_scan,
    get_list_scans,
    get_scan_by_id,
    update_scan_status,
)


async def test_create_scan_success():
    """
    Проверяет успешное создание строки скана в БД.
    """
    package, ecosystem = "some-package", "pypi"

    result = await create_scan(package, ecosystem)

    assert result.scan_id is not None
    assert result.root_package == package
    assert result.root_ecosystem == ecosystem
    assert result.status == "pending"
    assert result.total_nodes == 0
    assert result.report == ""
    assert isinstance(result.created_at, datetime)
    assert result.completed_at is None


async def test_get_scan_by_id_success(create_test_scan):
    """
    Проверяет возврат скана по его номеру.
    """
    existed_scan_id = create_test_scan.scan_id

    result = await get_scan_by_id(existed_scan_id)
    assert result is not None
    assert result.root_package == "test-package"


async def test_get_scan_by_id_not_found():
    """
    Проверка None если запись по айди не найдена.
    """
    assert await get_scan_by_id(999) is None


async def test_count_and_get_list_scans_success():
    """
    Проверка функции подсчета записей в БД и функции отображения записей списком.
    """
    for i in range(1, 10):
        await create_scan(f"package-n-{i}", "pypi")

    assert await count_scans() == 9

    first_resluts = await get_list_scans(5)
    assert len(first_resluts) == 5

    last_results = await get_list_scans(5, 5)
    assert len(last_results) == 4


async def test_update_scan_status_success(create_test_scan):
    """
    Проверка изменения статуса записи в БД.
    """
    existed_scan_id = create_test_scan.scan_id

    assert await update_scan_status(existed_scan_id, "new status") is True

    updated_scan = await get_scan_by_id(existed_scan_id)
    assert updated_scan is not None
    assert updated_scan.status == "new status"
