from src.database.tables.tables import Scan


async def create_scan(
    root_package: str,
    root_ecosystem: str,
) -> Scan:
    """
    Создает новый скан со статусом pending.
    """
    scan = await Scan.objects().create(
        root_package=root_package,
        root_ecosystem=root_ecosystem,
        status="pending",
        total_nodes=0,
    )

    return scan


async def get_scan_by_id(scan_id: int) -> Scan | None:
    """
    Возвращает скан по номеру ID или None если его нет в БД.
    """
    return await Scan.objects().where(Scan.scan_id == scan_id).first()


async def get_list_scans(
    limit: int = 20,
    offset: int = 0,
) -> list[Scan]:
    """
    Возвращает список сканов с пагинацией по сортировке даты создания.
    """
    scans = (
        await Scan.objects().order_by(Scan.created_at, ascending=False).limit(limit).offset(offset)
    )
    return list(scans)


async def count_scans() -> int:
    """
    Возвращает общее количество сканов.
    """
    return await Scan.count()


async def update_scan_status(scan_id: int, new_status: str) -> bool:
    """
    Обновить статус скана. Возвращает True если успешно.
    """
    updated_rows = (
        await Scan.update({Scan.status: new_status})
        .where(Scan.scan_id == scan_id)
        .returning(Scan.scan_id)
    )
    return len(updated_rows) > 0
