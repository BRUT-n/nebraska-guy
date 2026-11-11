from datetime import datetime

import httpx
import pytest
import respx
from src.clients.github import GITHUB_API_URL, get_contributors_count, get_last_commit_at, get_repo
from src.exceptions import NoCommitsError, RepoNotFoundError
from src.models.github import GitHubRepoInfo

OWNER = "brut-n"
REPO = "nebraska-guy"
BASE_GIT_URL = f"{GITHUB_API_URL}/repos/{OWNER}/{REPO}"
URL_FOR_CONTRIBUTORS_COUNT = f"{BASE_GIT_URL}/contributors?per_page=1&anon=true"
URL_FOR_LAST_COMMIT = f"{GITHUB_API_URL}/repos/{OWNER}/{REPO}/commits?per_page=1"


@respx.mock
async def test_get_repo_success():
    """
    Проверяет успешное получение данных для GitHubRepoInfo.
    """
    mock_git_json = {"stargazers_count": 1, "archived": False, "pushed_at": "2026-10-27T15:23:28Z"}

    respx.get(BASE_GIT_URL).mock(return_value=httpx.Response(200, json=mock_git_json))

    result = await get_repo(OWNER, REPO)

    assert isinstance(result, GitHubRepoInfo)
    assert result.owner == OWNER
    assert result.name == REPO
    assert result.stars == 1
    assert result.archived is False
    assert isinstance(result.pushed_at, datetime)
    assert result.pushed_at == datetime.fromisoformat("2026-10-27T15:23:28Z")


@respx.mock
async def test_get_repo_not_found():
    """
    Проверка выброса RepoNotFoundError если репозиторий не найден.
    """
    respx.get(BASE_GIT_URL).mock(return_value=httpx.Response(404))

    with pytest.raises(RepoNotFoundError) as exc_info:
        await get_repo(OWNER, REPO)

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
    Проверка ошбика RepoNotFoundError.
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
