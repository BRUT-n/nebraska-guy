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
