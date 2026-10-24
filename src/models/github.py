from datetime import datetime

from pydantic import BaseModel


class GitHubRepoInfo(BaseModel):
    """
    Метаданные репозитория GitHub.
    """

    owner: str
    name: str
    stars: int
    archived: bool
    pushed_at: datetime | None
