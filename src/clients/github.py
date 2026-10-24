import os
from datetime import datetime

import httpx

from src.exceptions import GitHubClientError, NoCommitsError, RepoNotFoundError
from src.models.github import GitHubRepoInfo

GITHUB_API_URL = "https://api.github.com"
USER_AGENT = "nebraska-guy/0.1.0 (https://github.com/BRUT-n/nebraska-guy)"
DEFAULT_TIMEOUT = httpx.Timeout(connect=5.0, read=15.0, write=5.0, pool=5.0)


def _get_headers() -> dict[str, str]:
    """
    Возвращает заголовки с токеном (если он есть).
    Без токена запросы к GitHub ограничены сильнее.
    """
    headers = {
        "User-Agent": USER_AGENT,
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2026-03-10",
    }
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    return headers


def _raise_rate_limit(response: httpx.Response) -> None:
    """
    Ловит лимит запросов и выбрасывает ошибку собирая заголовки от GitHub.
    remaining - сколько запросов осталось.
    reset - через сколько сброс лимита.
    """
    remaining = response.headers.get("x-ratelimit-remaining", "?")
    reset = response.headers.get("x-ratelimit-reset", "?")
    raise GitHubClientError(f"Rate limit exceeded! Remaining={remaining} | Reset={reset}")


async def _request(
    method: str,
    url: str,
    params: dict | None = None,
) -> httpx.Response | None:
    """
    Хелпер для выполнения запросов к GitHub.
    Возвращает Response или None, если ресурс не найден (404).
    Бросает GitHubClientError при сетевых ошибках, HTTP-ошибках и rate limit.
    """
    try:
        async with httpx.AsyncClient(timeout=DEFAULT_TIMEOUT) as client:
            response = await client.request(
                method=method, url=url, headers=_get_headers(), params=params
            )
    except httpx.TimeoutException as exc:
        raise GitHubClientError(f"Timeout for {url}") from exc
    except httpx.ConnectError as exc:
        raise GitHubClientError(f"Connection error for {url}") from exc

    if response.status_code == httpx.codes.NOT_FOUND:
        return None

    if response.status_code in (httpx.codes.FORBIDDEN, httpx.codes.TOO_MANY_REQUESTS):
        _raise_rate_limit(response)

    try:
        # ловит необработанные ошибки
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        raise GitHubClientError(f"HTTP {exc.response.status_code} for {url}") from exc
    return response


async def get_repo(owner: str, repo: str) -> GitHubRepoInfo:
    """
    Получает метаданные репозитория.
    None - если репо не найден.
    """
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}"
    response = await _request("GET", url)
    if response is None:
        raise RepoNotFoundError(f"Repo '{owner}/{repo}' not found on GitHub")

    data = response.json()
    return GitHubRepoInfo(
        owner=owner,
        name=repo,
        stars=data.get("stargazers_count", 0),
        archived=data.get("archived", False),
        pushed_at=data.get("pushed_at"),
    )


async def get_contributors_count(owner: str, repo: str) -> int:
    """
    Возвращает количество контрибьюторов или None, если репо не найден.
    """
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/contributors"

    # Общее число авторов вычисляется по номеру последней страницы
    # Поэтому запрос 1 элемента (контрибьютора) на страницу
    params = {"per_page": 1, "anon": "true"}

    response = await _request("GET", url, params)
    if response is None:
        raise RepoNotFoundError(f"Cannot get contributors: Repository '{owner}/{repo}' not found")

    # В GitHub API нет прямого поля "contributors_count".
    # ТРЮК: Мы смотрим на служебный HTTP-заголовок 'Link'.
    # Если страниц много, GitHub возвращает ссылку на последнюю страницу (rel="last").
    # Так как на одной странице у нас ровно 1 объект (per_page=1),
    # то номер последней страницы равен общему количеству контрибьюторов.
    if "last" in response.links:
        last_url = response.links["last"]["url"]
        page_number = httpx.URL(last_url).params.get("page")
        if page_number and page_number.isdigit():
            return int(page_number)

    # Если ссылки "last" в заголовках нет, значит, страниц больше одной не появилось.
    # Все авторы (0 или 1 человек) уместились в первый единственный ответ.
    # В этом случае просто возвращаем количество элементов в JSON-массиве.
    return len(response.json())


async def get_last_commit_at(owner: str, repo: str) -> datetime:
    """
    Возвращает дату последнего коммита или None, если коммитов нет.
    """
    url = f"{GITHUB_API_URL}/repos/{owner}/{repo}/commits"
    # параметр на самый свежий коммит
    params = {"per_page": 1}
    response = await _request("GET", url, params)
    if response is None:
        raise RepoNotFoundError(f"Cannot get last commit: Repository '{owner}/{repo}' not found")

    data = response.json()
    if not data:
        raise NoCommitsError(f"Repository '{owner}/{repo}' has no commits yet")

    commit_date_str = data[0]["commit"]["author"]["date"]
    return datetime.fromisoformat(commit_date_str)
