from urllib.parse import urlparse

from src.models.pypi import PyPIPackageInfo

_GITHUB_HOSTS = {"github.com", "www.github.com"}

_PRIORITY_URL_KEYS = (
    "source",
    "repository",
    "code",
    "github",
    "sourcecode",
    "homepage",
    "home",
)

_NON_REPO_PREFIXES = {
    "orgs",
    "users",
    "topics",
    "trending",
    "marketplace",
    "features",
    "about",
    "sponsors",
    "settings",
    "notifications",
    "search",
    "explore",
    "collections",
    "pricing",
    "security",
    "customer-stories",
    "readme",
    "site",
    "contact",
    "privacy",
    "terms",
    "git-guides",
}


def _parse_github_url(url: str) -> tuple[str, str] | None:
    """
    Парсит URL отсекая лишние ссылки и пути.
    Возвращает (owner, repo) для GitHub-репо, иначе None.
    Парсит ссылки типа {протокол}://{хост}... через urlparse
    """
    if not url:
        return None

    try:
        parsed = urlparse(url)
    except ValueError:
        return None

    if parsed.netloc.lower() not in _GITHUB_HOSTS:
        return None

    path_parts = [part for part in parsed.path.split("/") if part]
    if len(path_parts) < 2:
        return None

    owner, repo = path_parts[0], path_parts[1]

    if owner.lower() in _NON_REPO_PREFIXES:
        return None

    repo = repo.removesuffix(".git")
    if not repo:
        return None

    return owner, repo


def _yield_all_package_urls(info: PyPIPackageInfo):
    """
    Отдает ссылки из пакета по очередности приоритета.
    Собирает словарь с форматированием ->
    Проверяет project_urls по приоритетным ключам ->
    Проверяет остальные ссылки ->
    затем home_page.
    """
    if info.project_urls:
        # сбор словаря с ключами после форматирования
        norm_urls = {
            key.lower().replace(" ", "").replace("-", "").replace("_", ""): url
            for key, url in info.project_urls.items()
        }

        # итерация по приоритетным ключам
        for key in _PRIORITY_URL_KEYS:
            if url := norm_urls.get(key):
                yield url

        # итерация по всем ссылкам
        for url in norm_urls.values():
            if url:
                yield url

    # проверка последнего возможного источника
    if info.home_page:
        yield info.home_page


def extract_github_repo(info: PyPIPackageInfo) -> tuple[str, str] | None:
    """
    Извлекает owner, repo из метаданных PyPI-пакета.
    Возвращает None, если ссылка на GitHub не найдена.
    """
    # переменная накапливает проверенные ссылки
    seen_urls: set[str] = set()

    for url in _yield_all_package_urls(info):
        if url in seen_urls:
            continue
        seen_urls.add(url)

        if result := _parse_github_url(url):
            return result

    return None
