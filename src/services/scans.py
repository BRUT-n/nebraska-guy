from src.database.crud import scans as crud_scans
from src.database.tables.tables import Scan


async def create_new_scan(
    root_package: str,
    root_ecosystem: str,
) -> Scan:
    """
    Создает новый скан.
    Postgres - Neo4j - Celery (в следующих итерациях)
    """
    return await crud_scans.create_scan(root_package=root_package, root_ecosystem=root_ecosystem)


async def get_scan(scan_id: int) -> Scan | None:
    """Возвращает скан по ID или None."""
    return await crud_scans.get_scan_by_id(scan_id)


async def list_all_scans(limit: int, offset: int) -> list[Scan]:
    """Возвращает список сканов с пагинацией."""
    return await crud_scans.get_list_scans(limit=limit, offset=offset)


async def get_scans_count() -> int:
    """Возвращает общее количество сканов."""
    return await crud_scans.count_scans()
