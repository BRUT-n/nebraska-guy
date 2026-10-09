from datetime import datetime
from enum import StrEnum, auto

from pydantic import BaseModel, ConfigDict, field_validator

from src.models.utils import is_valid_package_name, normalize_package_name


class Ecosystem(StrEnum):
    PYPI = auto()
    # NPM = auto()


class ScanCreateSchema(BaseModel):
    """
    Схема для создания скана. Данные присылает пользователь.
    Встроена валидация и нормализация имени пакета.
    """

    root_package: str
    root_ecosystem: Ecosystem = Ecosystem.PYPI

    @field_validator("root_package")
    @classmethod
    def validate_and_normalize_package_name(cls, v: str) -> str:
        """
        Валидатор Pydantic
        """
        is_valid, error = is_valid_package_name(v)
        if not is_valid:
            raise ValueError(f"Некорректное имя пакета: {error}")
        return normalize_package_name(v)


class ScanReadSchema(BaseModel):
    """
    Схема для чтения скана. Все поля из Postgres-модели.
    """

    scan_id: int
    root_package: str
    root_ecosystem: str
    status: str
    total_nodes: int
    error_message: str | None
    report: str | None
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None

    model_config = ConfigDict(from_attributes=True)
