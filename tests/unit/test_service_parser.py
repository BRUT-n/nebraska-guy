import pytest
from packaging.requirements import Requirement
from src.exceptions import InvalidDependencyString
from src.services.dependency_parser import (
    is_runtime_dependency,
    parse_requirement,
    parse_requirements,
)


@pytest.mark.parametrize(
    "raw_requirement, expected_result",
    [
        ("request", True),
        ("starlette>=0.46.0", True),
        ('opentelemetry-sdk>=1.44.0; extra == "opentelemetry"', False),
        ('PySocks!=1.5.7,>=1.5.6; extra == "socks"', False),
        ('tzdata; platform_system == "Windows" and extra == "timezone"', False),
        ("neo4j~=6.1.0", True),
        ('pre-commit; extra == "dev"', False),
        ('neo4j-rust-ext~=6.1.0.0; extra == "rust-driver-ext"', False),
    ],
    ids=[
        "no-marker",
        "version-marker",
        "extra-marker",
        "more-version-markers",
        "platform-marker",
        "tilda-version",
        "dev-extra",
        "tilda-version-with-extra",
    ],
)
def test_is_runtime_dependency(raw_requirement, expected_result):
    """
    Проверяет различные варианты приходящих данных по зависимостям.
    """
    req = Requirement(raw_requirement)
    assert is_runtime_dependency(req=req) is expected_result


@pytest.mark.xfail(reason="TODO в функции: текстовый поиск 'extra' ломает обработку !='dev'")
def test_is_runtime_dependency_inverted_marker_BUG():
    """
    Проверяет инвертированный маркер extra != 'dev'. Сейчас это баг.
    """
    req = Requirement('package; extra != "dev"')
    assert is_runtime_dependency(req=req) is True


@pytest.mark.parametrize(
    "raw, expected_name, expected_version_spec, expected_dep_type, expected_extras",
    [
        ("charset_normalizer<4,>=2", "charset-normalizer", "<4,>=2", "runtime", []),
        ("zope.interface", "zope-interface", None, "runtime", []),
        (
            "aiohttp[speedups]<4.0.0,>=3.12.15",
            "aiohttp",
            "<4.0.0,>=3.12.15",
            "runtime",
            ["speedups"],
        ),
    ],
)
def test_parse_requirement_valid_runtime(
    raw, expected_name, expected_version_spec, expected_dep_type, expected_extras
):
    """
    Проверяет парсинг зависимостей по валидным данным.
    """
    result = parse_requirement(raw=raw)

    assert result is not None
    assert result.name == expected_name
    assert result.version_spec == expected_version_spec
    assert result.dependency_type == expected_dep_type
    assert result.extras == expected_extras


@pytest.mark.parametrize(
    "raw",
    [
        ('PySocks!=1.5.7,>=1.5.6; extra == "socks"'),
        ('test; extra == "test"'),
        ('develop==1.0.0; extra == "dev"'),
    ],
)
def test_parse_requirement_non_runtime(raw):
    """
    Проверяет None если зависимость не runtime (есть маркер extra).
    """
    assert parse_requirement(raw=raw) is None


@pytest.mark.parametrize("invalid_raw", [("idna=2.5"), (">= 2.5.0"), ("package!")])
def test_parse_requirement_invalid_raises(invalid_raw):
    """
    Проверяет ошибку на парсинг невалидных данных
    """
    with pytest.raises(InvalidDependencyString):
        parse_requirement(invalid_raw)


def test_parse_requirements_none_returns_empty_list():
    """
    Проверяет возврат пустого списка если зависимостей нет.
    """
    assert parse_requirements(None) == []


def test_parse_requirements_empty_list_returns_empty_list():
    """
    Проверяет возврат пустого списка если все зависимости не прошли проверку по типу.
    """
    assert parse_requirements([]) == []


def test_parse_requirements_filters_out_non_runtime():
    """
    Проверяет фильтрацию зависимостей. Возвращается только список с типом runtime.
    """
    raw_list = [
        "requests>=2.0",
        'pytest; extra == "dev"',
        "urllib3; python_version >= '3.8'",
        'black; extra == "test"',
    ]
    result = parse_requirements(raw_list)

    assert len(result) == 2
    assert {dep.name for dep in result} == {"requests", "urllib3"}


def test_parse_requirements_raises_on_invalid_string():
    """
    Проверяет ошибку на невалидность PEP 508 данных.
    Если хоть один элемент невалидный, функция падает.
    """
    raw_list = ["requests", "this is not valid!!!"]
    with pytest.raises(InvalidDependencyString):
        parse_requirements(raw_list)
