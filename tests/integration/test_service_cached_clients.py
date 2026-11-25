from datetime import UTC, datetime
from unittest.mock import AsyncMock

import pytest
from src.core.cache import cache_get, cache_set
from src.models.pypi import PyPIPackageInfo
from src.services.cached_clients import (
    cached_github_repo,
    cached_pypi_package,
)


@pytest.mark.asyncio(loop_scope="session")
async def test_cached_pypi_package_from_source_not_cache(monkeypatch):
    """
    Проверяет получение данных из pypi, если данных нет в кеше.
    """
    info = PyPIPackageInfo(
        name="some-package", version="<=1.0", requires_dist=None, project_urls=None, home_page=None
    )
    get_package_mock = AsyncMock(return_value=info)
    monkeypatch.setattr("src.services.cached_clients.get_package", get_package_mock)

    result = await cached_pypi_package("some-package")
    assert result == info

    cache_raw = await cache_get("pypi:some-package")
    assert isinstance(cache_raw, dict)
    assert cache_raw == info.model_dump()


@pytest.mark.asyncio(loop_scope="session")
async def test_cached_pypi_package_from_cache(monkeypatch):
    """
    Проверяет получение данных из кеша, без обращения к pypi.
    """
    info_for_cache = PyPIPackageInfo(
        name="some-package-cached",
        version="<=1.0",
        requires_dist=None,
        project_urls=None,
        home_page=None,
    )
    get_package_mock = AsyncMock()
    monkeypatch.setattr("src.services.cached_clients.get_package", get_package_mock)

    await cache_set("pypi:some-package-cached", info_for_cache.model_dump(), 60)

    result_cache = await cached_pypi_package("some-package-cached")

    assert isinstance(result_cache, PyPIPackageInfo)
    assert result_cache == info_for_cache
    get_package_mock.assert_not_called()


@pytest.mark.asyncio(loop_scope="session")
async def test_cached_github_repo_from_source_not_cache(monkeypatch):
    """
    Проверяет получение данных из github, если данных нет в кеше.
    """
    commit_dt = datetime(2026, 11, 24, 18, 0, tzinfo=UTC)
    repo_data = {
        "stars": 60,
        "is_archived": False,
        "contributions_count": 5,
        "last_commit_at": commit_dt,
    }
    fetch_repo_info_for_node_mock = AsyncMock(return_value=repo_data)
    monkeypatch.setattr(
        "src.services.cached_clients.fetch_repo_info_for_node", fetch_repo_info_for_node_mock
    )

    result = await cached_github_repo("owner", "repo")

    assert result == repo_data
    assert isinstance(result["last_commit_at"], datetime)
    fetch_repo_info_for_node_mock.assert_awaited_once_with("owner", "repo")

    cache_raw = await cache_get("github:owner/repo")
    assert isinstance(cache_raw, dict)
    assert cache_raw["stars"] == 60
    assert cache_raw["is_archived"] is False
    assert cache_raw["contributions_count"] == 5
    assert cache_raw["last_commit_at"] == commit_dt.isoformat()


@pytest.mark.asyncio(loop_scope="session")
async def test_cached_github_repo_from_cache(monkeypatch):
    """
    Проверяет получение данных из кеша, без обращения к github.
    """
    commit_dt = "2026-11-24T18:00:00+00:00"
    info_for_cache = {
        "stars": 60,
        "is_archived": False,
        "contributors_count": 5,
        "last_commit_at": commit_dt,
    }
    fetch_repo_info_for_node_mock = AsyncMock()
    monkeypatch.setattr(
        "src.services.cached_clients.fetch_repo_info_for_node", fetch_repo_info_for_node_mock
    )
    await cache_set("github:cached-owner/cached-repo", info_for_cache, 60)

    result_cache = await cached_github_repo("cached-owner", "cached-repo")

    fetch_repo_info_for_node_mock.assert_not_called()

    assert isinstance(result_cache["last_commit_at"], datetime)
    assert result_cache["last_commit_at"] == datetime.fromisoformat(commit_dt)
    assert result_cache["stars"] == 60
    assert result_cache["is_archived"] is False
    assert result_cache["contributors_count"] == 5
