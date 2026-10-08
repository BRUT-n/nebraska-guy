import os

from dotenv import load_dotenv

load_dotenv()


def build_neo4j_url() -> str:
    """
    Собирает URL подключения из переменных окружения
    """
    user = os.environ.get("NEO4J_USERNAME", "neo4j")
    password = os.environ["NEO4J_PASSWORD"]
    host = os.environ.get("NEO4J_HOST", "localhost")
    port = os.environ.get("NEO4J_BOLT_PORT", "7687")
    return f"bolt://{user}:{password}@{host}:{port}"
