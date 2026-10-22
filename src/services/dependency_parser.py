from packaging.requirements import InvalidRequirement, Requirement

from src.exceptions import InvalidDependencyString
from src.models.requirement import DependencyType, ParsedDependency
from src.models.utils import normalize_package_name


def is_runtime_dependency(req: Requirement) -> bool:
    """
    Возвращает True если зависимость является runtime.
    Runtime — это зависимость, которая ставится по умолчанию
    (без запроса конкретной extra). Условия окружения
    (python_version, os_name) игнорируются.

    TODO на будущее:
    1. Избавиться от текстового поиска "extra", так как он может ловить
       имена других переменных или ОС (например, os_name == 'extranos').
    2. Реализовать обработку через packaging разные кавычки, пробелы и логику AND/OR.
    3. Учесть инвертированные маркеры вида `extra != 'dev'`.
    """
    if req.marker is None:
        return True

    marker_str = str(req.marker).lower().replace(" ", "")

    # если нет extra - runtime
    if "extra" not in marker_str:
        return True

    # Пустая extra - runtime
    # Во всех остальных случаях (конкретные dev, test или socks)
    # срезаем угол и скипаем пакет, чтобы не усложнять код.
    return "extra==''" in marker_str or 'extra==""' in marker_str


def parse_requirement(raw: str) -> ParsedDependency | None:
    """
    Парсит строку requires_dist.
    Возвращает ParsedDependency, если зависимость runtime.
    Возвращает None, если зависимость требует extra (не runtime).
    Бросает InvalidDependencyString, если строка невалидна.
    """
    try:
        req = Requirement(raw)
    except InvalidRequirement as exc:
        raise InvalidDependencyString(f"Invalid requirement: {raw!r}") from exc

    if not is_runtime_dependency(req):
        return None

    return ParsedDependency(
        name=normalize_package_name(req.name),
        version_spec=str(req.specifier) if req.specifier else None,
        dependency_type=DependencyType.RUNTIME,
        extras=sorted(req.extras),
    )


def parse_requirements(raw_list: list[str] | None) -> list[ParsedDependency]:
    """
    Парсит список строк, собирает runtime-зависимости в список.
    Исключает None (не runtime) из списка после обработки зависимости по типу.
    """
    if not raw_list:
        return []

    results = [parse_requirement(raw) for raw in raw_list]
    return [dep for dep in results if dep is not None]
