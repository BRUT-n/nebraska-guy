import asyncio
import logging

from fastapi import APIRouter, HTTPException, Path, Query, status
from pydantic import TypeAdapter
from src.models.scan import ScanCreateSchema, ScanReadSchema
from src.services import scans as scans_service
from src.services.crawler import run_scan

router = APIRouter(prefix="/scans", tags=["scans"])

scans_list_adapter = TypeAdapter(list[ScanReadSchema])


logger = logging.getLogger(__name__)

_background_tasks: set[asyncio.Task] = set()


async def _run_scan_background_safe(scan_id: int, root_package: str) -> None:
    """
    Обертка для безопасного фонового выполнения функции run_scan.
    Используется для отслеживания ошибок при выполнении в фоне.
    """
    try:
        await run_scan(scan_id, root_package)
    except Exception:
        logger.exception("Background scan %d for %s crashed", scan_id, root_package)


@router.post(
    "",
    response_model=ScanReadSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_scan(payload: ScanCreateSchema) -> ScanReadSchema:
    """
    Создает новую запись о скане в Postgres и отдает пользователю.
    Запускает фоновую задачу краулера в текущем event loop ->
    удаляет задачу из памяти после завершения.
    """
    scan = await scans_service.create_new_scan(
        root_package=payload.root_package,
        root_ecosystem=payload.root_ecosystem,
    )

    task = asyncio.create_task(
        _run_scan_background_safe(scan_id=scan.scan_id, root_package=scan.root_package),
        name=f"scan-{scan.scan_id}",
    )

    _background_tasks.add(task)
    task.add_done_callback(_background_tasks.discard)

    logger.info(
        "Queued scan %d for %s (task=%s)",
        scan.scan_id,
        payload.root_package,
        task.get_name(),
    )

    return ScanReadSchema.model_validate(scan)


@router.get("/{scan_id}", response_model=ScanReadSchema)
async def get_scan(
    scan_id: int = Path(..., gt=0, description="Идентификатор скана"),
) -> ScanReadSchema:
    """
    Получить скан по его ID.
    """
    scan = await scans_service.get_scan(scan_id=scan_id)
    if scan is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Scan with id={scan_id} not found",
        )
    return ScanReadSchema.model_validate(scan)


@router.get(
    "",
    response_model=list[ScanReadSchema],
)
async def get_list_scans(
    limit: int = Query(
        default=10,
        ge=1,
        le=20,
        description="Максимальное количество возвращаемых сканов",
    ),
    offset: int = Query(default=0, ge=0, description="Смещение для итерации по страницам"),
) -> list[ScanReadSchema]:
    """
    Возвращает список сканов с пагинацией.
    """
    scans = await scans_service.list_all_scans(limit=limit, offset=offset)
    return scans_list_adapter.validate_python(scans)
