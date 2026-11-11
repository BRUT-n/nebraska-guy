import os

import pytest
import pytest_asyncio
from neomodel import adb
from src.database.graph_models import PackageNode, ScanNode
from src.database.tables.tables import Scan
from testcontainers.community.neo4j import Neo4jContainer
from testcontainers.community.postgres import PostgresContainer


@pytest.fixture(scope="session", autouse=True)
def setup_containers():
    """
    Запускает тестовые контейнеры и собирает переменные для подключения.
    Меняет переменные через os.environ с проектных на тестовые.
    """
    print("\n[Testcontainers] Запуск Postgres и Neo4j...")

    with (
        PostgresContainer("postgres:17-alpine") as psg,
        Neo4jContainer("neo4j:5-community") as neo4j,
    ):
        os.environ["POSTGRES_USER"] = psg.username
        os.environ["POSTGRES_PASSWORD"] = psg.password
        os.environ["POSTGRES_DB"] = psg.dbname
        os.environ["POSTGRES_HOST"] = psg.get_container_host_ip()
        os.environ["POSTGRES_PORT"] = str(psg.get_exposed_port(5432))

        os.environ["NEO4J_USERNAME"] = neo4j.username
        os.environ["NEO4J_PASSWORD"] = neo4j.password
        os.environ["NEO4J_HOST"] = neo4j.get_container_host_ip()
        os.environ["NEO4J_BOLT_PORT"] = str(neo4j.get_exposed_port(7687))

        os.environ["GITHUB_TOKEN"] = "fake-github-token"  # noqa: S105

        yield


@pytest_asyncio.fixture(scope="session", autouse=True)
async def neo4j_db_connection(setup_containers):
    """
    Устанавливает глобальное соединение c Neo4j для neomodel.
    """
    from src.settings import build_neo4j_url

    db_url = build_neo4j_url()

    await adb.set_connection(db_url)
    yield
    await adb.close_connection()


@pytest_asyncio.fixture(scope="session", autouse=True)
async def setup_database(setup_containers, neo4j_db_connection):
    """
    Создает таблицы в Postgres и схему в Neo4j.
    Содержит ленивые иморты для работы в рамках тестовых переменных окружения.
    """
    from src.database.graph_schema import install_graph_schema
    from src.database.tables.tables import Scan

    print("\n[DB] Создание таблиц Postgres...")
    await Scan.create_table(if_not_exists=True)

    print("\n[DB] Установка схемы Neo4j...")
    await install_graph_schema()

    yield


@pytest_asyncio.fixture(scope="function", autouse=True)
async def clean_databases(setup_database, neo4j_db_connection):
    """
    Чистит базу данных перед каждым тестом для изоляции.
    Содержит ленивые иморты для работы в рамках тестовых переменных окружения.
    """
    from src.database.tables.tables import Scan

    await Scan.delete(force=True)

    # await adb.cypher_query(
    #     "MATCH (n) WHERE n:ScanNode OR n:PackageNode DETACH DELETE n"
    # )
    await adb.cypher_query("MATCH (n) DETACH DELETE n")

    yield


@pytest_asyncio.fixture(scope="function")
async def create_test_scan():
    """
    Фикстура создает запись скана в БД.
    """
    scan_raw = Scan(
        root_package="test-package",
        root_ecosystem="pypi",
        status="pending",
    )

    await scan_raw.save()
    return scan_raw


@pytest_asyncio.fixture(scope="function")
async def create_test_scan_node():
    """
    Фикстура создает нод скана в графовой БД.
    """
    scan_node = ScanNode(scan_id=1, root_package="test-scan-node", status="test")
    await scan_node.save()
    return scan_node


@pytest_asyncio.fixture(scope="function")
async def create_test_package_node():
    """
    Фикстура создает нод пакета в графовой БД.
    """
    package_node = PackageNode(
        scan_id=1, name="test-package-node", ecosystem="pypi", stars=5, contributors_count=1
    )
    await package_node.save()
    return package_node
