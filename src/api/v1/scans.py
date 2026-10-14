from fastapi import APIRouter, HTTPException, Path, Query, status
from pydantic import TypeAdapter
from src.models.scan import ScanCreateSchema, ScanReadSchema
from src.services import scans as scans_service

router = APIRouter(prefix="/scans", tags=["scans"])

scans_list_adapter = TypeAdapter(list[ScanReadSchema])


@router.post(
    "",
    response_model=ScanReadSchema,
    status_code=status.HTTP_201_CREATED,
)
async def create_scan(payload: ScanCreateSchema) -> ScanReadSchema:
    """
    Создает новый скан.
    """
    scan = await scans_service.create_new_scan(
        root_package=payload.root_package,
        root_ecosystem=payload.root_ecosystem,
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
