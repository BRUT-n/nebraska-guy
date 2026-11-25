from datetime import datetime
from logging import getLogger

from src.clients.github import fetch_repo_info_for_node
from src.clients.pypi import get_package
from src.core.cache import cache_get, cache_set
from src.models.pypi import PyPIPackageInfo

logger = getLogger(__name__)

PYPI_TTL = 60 * 60 * 24
GITHUB_TTL = 60 * 60


def _pypi_key(name: str):
    """
    Форма ключа где источник данных pypi для записи в redis.
    """
    return f"pypi:{name}"


def _github_key(owner: str, repo: str):
    """
    Форма ключа где источник данных github для записи в redis.
    """
    return f"github:{owner}/{repo}"


async def cached_pypi_package(name: str) -> PyPIPackageInfo:
    """
    Возвращает PyPIPackageInfo из кеша если есть
    иначе берет из источника и записывает к кеш.
    """
    key = _pypi_key(name)
    cached = await cache_get(key)
    if cached is not None:
        logger.debug("Cache HIT for %s", key)
        return PyPIPackageInfo.model_validate(cached)

    logger.debug("Cache MISS for %s", key)
    info = await get_package(name)
    await cache_set(key, info.model_dump(), PYPI_TTL)
    return info


async def cached_github_repo(owner: str, repo: str) -> dict:
    """
    Возвращает словарь вида PackageNode из кеша если есть
    иначе берет из источника и записывает к кеш.
    """
    key = _github_key(owner, repo)
    cached = await cache_get(key)
    if cached is not None:
        logger.debug("Cache HIT for %s", key)
        if cached.get("last_commit_at"):
            cached["last_commit_at"] = datetime.fromisoformat(cached["last_commit_at"])
        return cached

    logger.debug("Cache MISS for %s", key)
    data = await fetch_repo_info_for_node(owner, repo)

    serializable = data.copy()
    if serializable.get("last_commit_at"):
        serializable["last_commit_at"] = serializable["last_commit_at"].isoformat()

    await cache_set(key, serializable, GITHUB_TTL)
    return data
