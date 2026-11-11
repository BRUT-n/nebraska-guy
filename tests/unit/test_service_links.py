from unittest.mock import Mock

import pytest
from src.services.github_link import _parse_github_url, _yield_all_package_urls, extract_github_repo


@pytest.mark.parametrize(
    "url",
    [
        (""),
        ("https://www.avatars.com/in/"),
        ("https://"),
        ("www.somehost.com"),
        ("github.com/page"),
        ("github.com/orgs/page"),
        ("github.com/owner"),
        ("https://github.com[trash]/owner/repo"),
    ],
    ids=[
        "empty-url",
        "full-url-not-git",
        "url-not-for-urlparse",
        "not-git-url",
        "short-length-to-unpacking",
        "non-repo-prefix",
        "missing-repo-path",
        "urlparse-value-error",
    ],
)
def test_parse_github_url_with_return_none(url):
    """
    Проверяет возврат None если условия успешного парсинга не выполнены.
    """
    assert _parse_github_url(url=url) is None


@pytest.mark.parametrize(
    "valid_url",
    [
        ("https://www.github.com/owner/repo"),
        ("github.com/owner/repo"),
        ("www.github.com/owner/repo.git"),
    ],
)
def test_parse_github_url_success(valid_url):
    """
    Проверяет корректный возврат владельца и репозитория
    """
    assert _parse_github_url(valid_url) == ("owner", "repo")


def test_yield_all_package_urls():
    """
    Проверяет сборку словаря ссылкок по очередности приоритетов.
    """
    pypi_info = Mock()
    pypi_info.home_page = "https://github.com/last-homepage"
    pypi_info.project_urls = {
        "source": "github.com/source",
        "repository": "github.com/repository",
        "code": "github.com/code",
        "github": "github.com/github",
        "sourcecode": "github.com/sourcecode",
        "home": "github.com/home",
        "Changelog": "github.com/changelog",
        "Documentation": "github.com/documentation",
    }

    urls_list = list(_yield_all_package_urls(pypi_info))

    assert urls_list.index("github.com/source") < urls_list.index("github.com/code")
    assert urls_list.index("github.com/repository") < urls_list.index("github.com/github")
    assert urls_list.index("github.com/home") < urls_list.index("github.com/documentation")
    assert urls_list[-1] == "https://github.com/last-homepage"


def test_extract_github_repo_success():
    """
    Проверяет успешное извлечение владельца и репозитория из словаря данных.
    """
    pypi_info = Mock()
    pypi_info.project_urls = {
        "home": "github.com/home",
        "source": "github.com/owner/repo",
        "Changelog": "github.com/changelog",
    }

    assert extract_github_repo(pypi_info) == ("owner", "repo")


def test_extract_github_repo_from_home_page():
    """
    Проверяет извлечение владельца и репозитория из поля home_page.
    """
    pypi_info = Mock()
    pypi_info.project_urls = {
        "home": "github.com/home",
        "source": "github.com/source",
        "Changelog": "github.com/changelog",
    }
    pypi_info.home_page = "github.com/home/page"

    assert extract_github_repo(pypi_info) == ("home", "page")


def test_extract_github_repo_return_none():
    """
    Проверяет возврат None если ссылки не содержат информацию.
    """
    pypi_info = Mock()
    pypi_info.project_urls = {
        "Changelog": "github.com/changelog",
    }
    pypi_info.home_page = "www.hostforpackage.com"

    assert extract_github_repo(pypi_info) is None
