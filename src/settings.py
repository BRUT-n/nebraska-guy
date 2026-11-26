import logging
import os

from dotenv import load_dotenv

load_dotenv()


def setup_logging() -> None:
    """
    Настраивает базовое логирование приложения из переменных окружения.
    """
    log_level_name = os.environ.get("LOG_LEVEL", "INFO")
    log_level = getattr(logging, log_level_name, logging.INFO)

    logging.basicConfig(
        level=log_level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def build_neo4j_url() -> str:
    """
    Собирает URL подключения для neo4j из переменных окружения.
    """
    user = os.environ.get("NEO4J_USERNAME", "neo4j")
    password = os.environ["NEO4J_PASSWORD"]
    host = os.environ.get("NEO4J_HOST", "localhost")
    port = os.environ.get("NEO4J_BOLT_PORT", "7687")
    return f"bolt://{user}:{password}@{host}:{port}"


def build_redis_url() -> str:
    """
    Собирает URL подключения redis из переменных окружения
    """
    host = os.environ.get("REDIS_HOST", "localhost")
    port = os.environ.get("REDIS_PORT", "6379")
    return f"redis://{host}:{port}/0"
