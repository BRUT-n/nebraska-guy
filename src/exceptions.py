class BaseAppError(Exception):
    """
    Базовое исключение приложения.
    """


class ExternalServiceError(BaseAppError):
    """
    Ошибка при обращении к внешнему сервису.
    """


class PyPIClientError(ExternalServiceError):
    """
    Базовая ошибка клиента PyPI.
    """


class PackageNotFoundError(PyPIClientError):
    """
    Пакен не найден в PyPI.
    """


class InvalidDependencyString(BaseAppError):
    """
    Строка зависимости не соответствует спецификации PEP 508.
    """


class GitHubClientError(ExternalServiceError):
    """
    Базовая ошибка клиента GitHub.
    """


class RepoNotFoundError(GitHubClientError):
    """
    Репозиторий не найден на GitHub.
    """


class NoCommitsError(GitHubClientError):
    """
    Репозиторий существует, но в нем нет коммитов.
    """
