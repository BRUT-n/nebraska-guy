import httpx
import pytest
import respx
from src.clients.pypi import PYPI_BASE_URL, get_package
from src.exceptions import PackageNotFoundError, PyPIClientError
from src.models.pypi import PyPIPackageInfo

PACKAGE_NAME = "datetime"
TARGET_PYPI_URL = f"{PYPI_BASE_URL}/{PACKAGE_NAME}/json"


@respx.mock
async def test_get_package_success():
    """
    Проверяет успешный возврат PyPIPackageInfo.
    """

    mock_pypi_json = {
        "info": {
            "name": "DateTime",
            "version": "6.0",
            "requires_dist": ["zope.interface", "pytz"],
            "project_urls": {"Homepage": "https://github.com/zopefoundation/DateTime"},
            "home_page": "https://github.com/zopefoundation/DateTime",
        }
    }

    respx.get(TARGET_PYPI_URL).mock(return_value=httpx.Response(200, json=mock_pypi_json))

    result = await get_package(PACKAGE_NAME)
    assert isinstance(result, PyPIPackageInfo)
    assert result.name == "DateTime"
    assert result.version == "6.0"
    assert isinstance(result.requires_dist, list)
    assert len(result.requires_dist) == 2
    assert result.project_urls == {"Homepage": "https://github.com/zopefoundation/DateTime"}


@respx.mock
async def test_get_package_not_found():
    """
    Проверяет ошибку PackageNotFoundError.
    """
    bad_package = "non-existent-package"
    url = f"{PYPI_BASE_URL}/{bad_package}/json"

    respx.get(url).mock(return_value=httpx.Response(404, json={"message": "Not Found"}))

    with pytest.raises(PackageNotFoundError) as exc_info:
        await get_package("non-existent-package")

    assert "Package 'non-existent-package' not found on PyPI" in str(exc_info.value)


@respx.mock
async def test_get_package_timeout():
    """
    Проверяет выброс PyPIClientError по таймуату.
    """
    respx.get(TARGET_PYPI_URL).mock(side_effect=httpx.TimeoutException("Timeout"))

    with pytest.raises(PyPIClientError) as exc_info:
        await get_package(PACKAGE_NAME)

    assert f"Timeout while fetching '{PACKAGE_NAME}'" in str(exc_info.value)


@respx.mock
async def test_get_package_connection_error():
    """
    Проверяет выброс PyPIClientError по ошибке подключения.
    """

    respx.get(TARGET_PYPI_URL).mock(side_effect=httpx.ConnectError("Network down"))

    with pytest.raises(PyPIClientError) as exc_info:
        await get_package(PACKAGE_NAME)

    assert f"Connection error while fetching '{PACKAGE_NAME}'" in str(exc_info.value)


@respx.mock
async def test_get_package_status_error():
    """
    Проверка выброса PyPIClientError по остальным ошибкам HTTP.
    """
    respx.get(TARGET_PYPI_URL).mock(return_value=httpx.Response(500))

    with pytest.raises(PyPIClientError) as exc_info:
        await get_package(PACKAGE_NAME)

    assert f"HTTP 500 while fetching '{PACKAGE_NAME}'" in str(exc_info.value)
