import httpx

from src.exceptions import PackageNotFoundError, PyPIClientError
from src.models.pypi import PyPIPackageInfo

PYPI_BASE_URL = "https://pypi.org/pypi"
USER_AGENT = "nebraska-guy/0.1.0 (https://github.com/BRUT-n/nebraska-guy)"
DEFAULT_TIMEOUT = httpx.Timeout(connect=5.0, read=15.0, write=5.0, pool=5.0)


async def get_package(name: str) -> PyPIPackageInfo:
    """
    Получает матаданные пакета по имени.
    PackageNotFoundError - когда пакета нет.
    PyPIClientError - при сбоях и таймаутах.
    """
    url = f"{PYPI_BASE_URL}/{name}/json"
    headers = {"User-Agent": USER_AGENT, "Accept": "application/json"}

    try:
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            response = await client.get(url, headers=headers)
    except httpx.TimeoutException as exc:
        raise PyPIClientError(f"Timeout while fetching '{name}'") from exc
    except httpx.ConnectError as exc:
        raise PyPIClientError(f"Connection error while fetching '{name}'") from exc

    if response.status_code == httpx.codes.NOT_FOUND:
        raise PackageNotFoundError(f"Package '{name}' not found on PyPI")

    try:
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise PyPIClientError(f"HTTP {exc.response.status_code} while fetching '{name}'") from exc

    data = response.json()

    return PyPIPackageInfo.model_validate(data["info"])
