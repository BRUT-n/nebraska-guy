from pydantic import BaseModel, ConfigDict


class PyPIPackageInfo(BaseModel):
    """
    Метаданные пакета из секции info ответа PyPI.
    """

    model_config = ConfigDict(extra="ignore")

    name: str
    version: str
    requires_dist: list[str] | None
    project_urls: dict[str, str] | None
    home_page: str | None = None
