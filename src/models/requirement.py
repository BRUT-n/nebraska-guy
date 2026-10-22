from enum import StrEnum, auto

from pydantic import BaseModel, Field


class DependencyType(StrEnum):
    """
    Тип зависимости пакета.
    """

    RUNTIME = auto()
    DEV = auto()
    OPTIONAL = auto()


class ParsedDependency(BaseModel):
    """
    Одна распарсенная зависимость из requires_dist.
    """

    name: str
    version_spec: str | None
    dependency_type: DependencyType
    extras: list[str] = Field(default_factory=list)
