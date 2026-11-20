from datetime import UTC, datetime

import httpx
import pytest
import respx
from src.clients.github import (
    GITHUB_API_URL,
    fetch_repo_info_for_node,
    get_contributors_count,
    get_last_commit_at,
    get_repo_base_info,
)
from src.exceptions import GitHubClientError, NoCommitsError, RepoNotFoundError
from src.models.github import GitHubRepoInfo

OWNER = "brut-n"
REPO = "nebraska-guy"
BASE_GIT_URL = f"{GITHUB_API_URL}/repos/{OWNER}/{REPO}"
URL_FOR_CONTRIBUTORS_COUNT = f"{BASE_GIT_URL}/contributors?per_page=1&anon=true"
URL_FOR_LAST_COMMIT = f"{GITHUB_API_URL}/repos/{OWNER}/{REPO}/commits?per_page=1"


@respx.mock
async def test_get_repo_base_info_success():
    """
    Проверяет успешное получение данных для GitHubRepoInfo.
    """
    mock_git_json = {"stargazers_count": 1, "archived": False, "pushed_at": "2026-10-27T15:23:28Z"}

    respx.get(BASE_GIT_URL).mock(return_value=httpx.Response(200, json=mock_git_json))

    result = await get_repo_base_info(OWNER, REPO)

    assert isinstance(result, GitHubRepoInfo)
    assert result.owner == OWNER
    assert result.name == REPO
    assert result.stars == 1
    assert result.archived is False
    assert isinstance(result.pushed_at, datetime)
    assert result.pushed_at == datetime.fromisoformat("2026-10-27T15:23:28Z")


@respx.mock
async def test_get_repo_base_info_not_found():
    """
    Проверка выброса RepoNotFoundError если репозиторий не найден.
    """
    respx.get(BASE_GIT_URL).mock(return_value=httpx.Response(404))

    with pytest.raises(RepoNotFoundError) as exc_info:
        await get_repo_base_info(OWNER, REPO)

    assert f"Repo '{OWNER}/{REPO}' not found on GitHub" in str(exc_info.value)


@respx.mock
async def test_get_contributors_count_success():
    """
    Проверяет успешное получение количества контрибьюторов где их больше одного.
    """
    link_url = 'https://api.github.com/repositories/1390708086/contributors?per_page=1&anon=true&page=75>; rel="last"'

    respx.get(URL_FOR_CONTRIBUTORS_COUNT).mock(
        return_value=httpx.Response(200, headers={"Link": link_url}, json={})
    )

    result = await get_contributors_count(OWNER, REPO)
    assert result == 75


@respx.mock
async def test_get_contributors_count_for_one():
    """
    Проверяет успешное получение одного контрибьютора.
    """
    respx.get(URL_FOR_CONTRIBUTORS_COUNT).mock(
        return_value=httpx.Response(200, json=[{"0": "user"}])
    )

    result = await get_contributors_count(OWNER, REPO)
    assert result == 1


@respx.mock
async def test_get_contributors_count_not_found():
    """
    Проверка ошибки RepoNotFoundError.
    Cannot get contributors если репозиторий не найден.
    """
    respx.get(URL_FOR_CONTRIBUTORS_COUNT).mock(return_value=httpx.Response(404))

    with pytest.raises(RepoNotFoundError) as exc_info:
        await get_contributors_count(OWNER, REPO)

    assert f"Cannot get contributors: Repository '{OWNER}/{REPO}' not found" in str(exc_info.value)


@respx.mock
async def test_get_last_commit_at_success():
    """
    Проверяет успешный возврат даты последнего коммита.
    """
    mock_git_json = [{"commit": {"author": {"date": "2026-10-26T17:14:41Z"}}}]

    respx.get(URL_FOR_LAST_COMMIT).mock(return_value=httpx.Response(200, json=mock_git_json))

    result = await get_last_commit_at(OWNER, REPO)
    assert result == datetime.fromisoformat("2026-10-26T17:14:41Z")


@respx.mock
async def test_get_last_commit_at_not_found():
    """
    Проверка ошибка RepoNotFoundError.
    Cannot get last commit если репозиторий не найден.
    """
    respx.get(URL_FOR_LAST_COMMIT).mock(return_value=httpx.Response(404))

    with pytest.raises(RepoNotFoundError) as exc_info:
        await get_last_commit_at(OWNER, REPO)

    assert f"Cannot get last commit: Repository '{OWNER}/{REPO}' not found" in str(exc_info.value)


@respx.mock
async def test_get_last_commit_at_no_commits():
    """
    Проверка ошибки NoCommitsError когда репозиторий пуст.
    """
    respx.get(URL_FOR_LAST_COMMIT).mock(return_value=httpx.Response(200, json=[]))

    with pytest.raises(NoCommitsError) as exc_info:
        await get_last_commit_at(OWNER, REPO)

    assert f"Repository '{OWNER}/{REPO}' has no commits yet" in str(exc_info)


async def test_fetch_repo_info_for_node_all_success(monkeypatch):
    """
    Проверяет успешное получение всех данных и их запись.
    last_commit перезаписывает pushed_at согласно логике исходной функции.
    """
    pushed_at = datetime(2026, 1, 1, tzinfo=UTC)
    commited_at = datetime(2026, 5, 5, tzinfo=UTC)

    async def get_repo_base_info_fake(owner, repo):
        """
        Подмена функции get_repo_base_info для получения данных.
        """
        return GitHubRepoInfo(
            owner=owner, name=repo, stars=500, archived=False, pushed_at=pushed_at
        )

    async def get_last_commit_at_fake(owner, repo):
        """
        Подмена функции get_last_commit_at для получения даты коммита.
        """
        return commited_at

    async def get_contributors_count_fake(owner, repo):
        """
        Подмена функции get_contributors_count для получения количества контрибьютеров.
        """
        return 30

    monkeypatch.setattr("src.clients.github.get_repo_base_info", get_repo_base_info_fake)
    monkeypatch.setattr("src.clients.github.get_last_commit_at", get_last_commit_at_fake)
    monkeypatch.setattr("src.clients.github.get_contributors_count", get_contributors_count_fake)

    result = await fetch_repo_info_for_node(OWNER, REPO)

    assert result["github_repo_url"] == f"https://github.com/{OWNER}/{REPO}"
    assert result["stars"] == 500
    assert result["is_archived"] is False
    assert result["last_commit_at"] == commited_at
    assert result["contributors_count"] == 30


async def test_fetch_repo_info_for_node_partial_failure(monkeypatch):
    """
    Проверяет частичную запись данных если один запрос не выполнился.
    """

    async def get_repo_base_info_fake(owner, repo):
        raise GitHubClientError("error")

    async def get_last_commit_at_fake(owner, repo):
        raise NoCommitsError("no commits")

    async def get_contributors_count_fake(owner, repo):
        return 30

    monkeypatch.setattr("src.clients.github.get_repo_base_info", get_repo_base_info_fake)
    monkeypatch.setattr("src.clients.github.get_last_commit_at", get_last_commit_at_fake)
    monkeypatch.setattr("src.clients.github.get_contributors_count", get_contributors_count_fake)

    result = await fetch_repo_info_for_node(OWNER, REPO)

    assert "stars" not in result
    assert "is_archived" not in result
    assert "last_commit_at" not in result
    assert result["contributors_count"] == 30
    assert result["github_repo_url"] == f"https://github.com/{OWNER}/{REPO}"
