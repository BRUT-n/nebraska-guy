import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from src.database.crud.nodes import create_package_node
from src.database.graph_models import PackageNode, ScanNode
from src.database.tables.tables import Scan
from src.exceptions import BaseAppError, PackageNotFoundError
from src.models.pypi import PyPIPackageInfo
from src.models.requirement import ParsedDependency
from src.services.crawler import CrawlContext, _get_or_create_package_node, _visit_package, run_scan


@pytest.mark.asyncio(loop_scope="session")
async def test_get_or_create_package_node_existing_package(create_test_package_node):
    """
    Проверяет возврат существующего в БД пакета.
    Зависимостей нет, счетчик нод не увеличился
    """
    ctx = CrawlContext(scan_id=create_test_package_node.scan_id)

    node, deps = await _get_or_create_package_node(ctx, create_test_package_node.name)

    assert node is not None
    assert deps == []
    assert node.scan_id == create_test_package_node.scan_id
    assert node.name == create_test_package_node.name
    assert ctx.nodes_count == 0


@pytest.mark.asyncio(loop_scope="session")
async def test_get_or_create_package_node_collect_data_from_clients(monkeypatch):
    """
    Проверка записи данных в БД после сбора данных клиентами PyPI и GitHub.
    Проверка увеличения счетчика созданных нод и проверка полученных зависимостей
    """
    ctx = CrawlContext(scan_id=1)

    get_package_mock = AsyncMock(
        return_value=PyPIPackageInfo(
            name="mock-name", version="1.0.0", requires_dist=["dep<=1.0", "dep"], project_urls=None
        )
    )
    extract_github_repo_mock = MagicMock()
    fetch_repo_info_for_node_mock = AsyncMock(
        return_value={
            "stars": 100,
            "contributors_count": 5,
            "is_archived": False,
            "github_repo_url": "https://github.com",
        }
    )
    monkeypatch.setattr("src.services.crawler.cached_pypi_package", get_package_mock)
    monkeypatch.setattr("src.services.crawler.extract_github_repo", extract_github_repo_mock)
    monkeypatch.setattr("src.services.crawler.cached_github_repo", fetch_repo_info_for_node_mock)

    node, deps = await _get_or_create_package_node(ctx, "package-to-create")

    assert ctx.nodes_count == 1
    assert isinstance(node, PackageNode)
    assert isinstance(deps, list)
    assert isinstance(deps[0], ParsedDependency)
    assert len(deps) == 2
    assert {d.name for d in deps} == {"dep"}
    assert node.scan_id == ctx.scan_id
    assert node.name == "package-to-create"
    assert node.version == "1.0.0"
    assert node.contributors_count == 5
    assert node.stars == 100
    assert node.is_archived is False


@pytest.mark.asyncio(loop_scope="session")
async def test_get_or_create_package_node_pypi_error(monkeypatch):
    """
    Проверка обработки ошибки от PyPI.
    Возврат пустых данных и появление пакета в ctx.failed_packages.
    """
    ctx = CrawlContext(scan_id=1)
    get_package_mock = AsyncMock(side_effect=PackageNotFoundError("Not found"))

    monkeypatch.setattr("src.services.crawler.cached_pypi_package", get_package_mock)

    node, deps = await _get_or_create_package_node(ctx, "broken-package")

    assert node is None
    assert deps == []
    assert "broken-package" in ctx.failed_packages
    assert ctx.nodes_count == 0


@pytest.mark.asyncio(loop_scope="session")
async def test_get_or_create_package_node_without_github(monkeypatch):
    """
    Проверка записи данных в БД после сбора данных клиентом PyPI, но без GitHub .
    """
    ctx = CrawlContext(scan_id=1)
    get_package_mock = AsyncMock(
        return_value=PyPIPackageInfo(
            name="mock-name", version="1.0.0", requires_dist=["dep<=1.0", "dep"], project_urls=None
        )
    )
    extract_github_repo_mock = MagicMock(return_value=None)
    monkeypatch.setattr("src.services.crawler.cached_pypi_package", get_package_mock)
    monkeypatch.setattr("src.services.crawler.extract_github_repo", extract_github_repo_mock)

    node, deps = await _get_or_create_package_node(ctx, "package-no-git")

    assert ctx.nodes_count == 1
    assert node is not None
    assert deps is not None
    assert node.scan_id == 1
    assert node.name == "package-no-git"
    assert node.ecosystem == "pypi"
    assert node.version == "1.0.0"
    assert node.contributors_count is None
    assert node.last_commit_at is None
    assert node.is_archived is None
    assert node.github_repo_url is None


@pytest.mark.asyncio(loop_scope="session")
async def test_visit_package_max_limit():
    """
    Проверка None если достигнут лимит нодов в БД.
    """
    ctx = CrawlContext(scan_id=1, max_nodes=10, nodes_count=10)
    result = await _visit_package(
        ctx=ctx,
        package_name="package",
        parent_node=None,
        depth=1,
        constraint="=1.0",
        dependency_type="runtime",
    )

    assert result is None


@pytest.mark.asyncio(loop_scope="session")
async def test_visit_package_not_exists(monkeypatch):
    """
    Проверка None если пакета не найдено в БД и невозможно получить из PyPI.
    """
    ctx = CrawlContext(scan_id=1)

    _get_or_create_package_node_mock = AsyncMock(return_value=(None, []))
    monkeypatch.setattr(
        "src.services.crawler._get_or_create_package_node", _get_or_create_package_node_mock
    )

    result = await _visit_package(ctx, "package", None, 1, ">1.0", "runtime")

    assert result is None


@pytest.mark.asyncio(loop_scope="session")
async def test_visit_package_creates_nodes_and_edges(monkeypatch):
    """
    Проверяет полный цикл обхода от корневого пакета до зависимостей.
    Создает узлы в графе, рекурсивно обходит зависимости и сохраненяет свойства связей:
    корневой -> зависимость1 -> зависимость 2.
    """
    ctx = CrawlContext(scan_id=1)

    # подготовка пакетов для мока (_visit_package -> _get_or_create_package_node -> get_package)
    root_package = PyPIPackageInfo(
        name="root_package",
        version=">=1.0.0",
        requires_dist=["dep1==1.0", "dep2>=1.0"],
        project_urls=None,
    )
    dep1_package = PyPIPackageInfo(
        name="dep1", version="==1.0", requires_dist=None, project_urls=None
    )
    dep2_package = PyPIPackageInfo(
        name="dep2", version=">=1.0", requires_dist=None, project_urls=None
    )
    monkeypatch.setattr(
        "src.services.crawler.cached_pypi_package",
        AsyncMock(side_effect=[root_package, dep1_package, dep2_package]),
    )

    result = await _visit_package(
        ctx=ctx,
        package_name="root_package",
        parent_node=None,
        depth=0,
        constraint=None,
        dependency_type="runtime",
    )

    assert result is not None
    assert result.name == "root_package"
    assert ctx.nodes_count == 3

    # проверка наличия нодов в БД
    depends_nodes = await result.depends_on.all()  # type: ignore[reportAttributeAccessIssue]
    assert len(depends_nodes) == 2
    assert {node.name for node in depends_nodes} == {"dep1", "dep2"}

    # проверка связей по каждому дочернему ноду
    nodes_name = {node.name: node for node in depends_nodes}
    rel_dep1 = await result.depends_on.relationship(nodes_name["dep1"])  # type: ignore[reportAttributeAccessIssue]
    assert rel_dep1.constraint == "==1.0"
    assert rel_dep1.dependency_type == "runtime"
    rel_dep2 = await result.depends_on.relationship(nodes_name["dep2"])  # type: ignore[reportAttributeAccessIssue]
    assert rel_dep2.constraint == ">=1.0"
    assert rel_dep2.dependency_type == "runtime"

    # проверка отсутствия связей у дочерних узлов
    assert await nodes_name["dep1"].depends_on.all() == []
    assert await nodes_name["dep2"].depends_on.all() == []


@pytest.mark.asyncio(loop_scope="session")
async def test_run_scan_completed(create_test_scan, monkeypatch):
    """
    Проверяет успешное завершение обхода пакетов и построение связей.
    """
    scan_id = create_test_scan.scan_id

    async def fake_visit_package(ctx, package_name, **kwargs):
        ctx.nodes_count += 1
        return await create_package_node(
            scan_id=ctx.scan_id,
            name=package_name,
            ecosystem="pypi",
            version="1.0.0",
        )

    monkeypatch.setattr("src.services.crawler._visit_package", fake_visit_package)

    result = await run_scan(scan_id, "test-package")

    assert result is not None
    assert isinstance(result, CrawlContext)
    assert result.scan_id == scan_id
    assert result.nodes_count == 1
    assert result.failed_packages == []

    # PostgreSQL
    scan_node = await Scan.objects().get(Scan.scan_id == scan_id)
    assert scan_node is not None
    assert scan_node.root_package == "test-package"
    assert scan_node.status == "completed"
    assert scan_node.total_nodes == 1

    # Neo4j
    updated_scan_node = await ScanNode.nodes.get(scan_id=scan_id)
    assert updated_scan_node is not None
    assert updated_scan_node.root_package == "test-package"
    assert updated_scan_node.status == "completed"

    edges = await updated_scan_node.includes.all()  # type: ignore[reportAttributeAccessIssue]
    assert len(edges) == 1
    assert edges[0].name == "test-package"


@pytest.mark.asyncio(loop_scope="session")
async def test_run_scan_partial(create_test_scan, monkeypatch):
    """
    Проверяет частичный успех выполнения обхода и запись проваленных пакетов.
    """
    scan_id = create_test_scan.scan_id

    async def fake_visit_package(ctx, package_name, **kwargs):
        ctx.nodes_count += 1
        ctx.failed_packages.append("broken-package")
        return await create_package_node(
            scan_id=ctx.scan_id,
            name=package_name,
            ecosystem="pypi",
            version="1.0.0",
        )

    monkeypatch.setattr("src.services.crawler._visit_package", fake_visit_package)

    result = await run_scan(scan_id, "test-package")

    assert result is not None
    assert isinstance(result, CrawlContext)
    assert result.scan_id == scan_id
    assert result.nodes_count == 1
    assert result.failed_packages == ["broken-package"]

    # PostgreSQL
    scan_node = await Scan.objects().get(Scan.scan_id == scan_id)
    assert scan_node is not None
    assert scan_node.root_package == "test-package"
    assert scan_node.status == "partial"
    assert scan_node.error_message is not None
    assert json.loads(scan_node.error_message) == {"failed_packages": ["broken-package"]}
    assert scan_node.total_nodes == 1

    # Neo4j
    updated_scan_node = await ScanNode.nodes.get(scan_id=scan_id)
    assert updated_scan_node is not None
    assert updated_scan_node.root_package == "test-package"
    assert updated_scan_node.status == "partial"

    edges = await updated_scan_node.includes.all()  # type: ignore[reportAttributeAccessIssue]
    assert len(edges) == 1
    assert edges[0].name == "test-package"


@pytest.mark.asyncio(loop_scope="session")
async def test_run_scan_failed(create_test_scan, monkeypatch):
    """
    Проверка BaseAppError если что то пошло не так.
    """
    scan_id = create_test_scan.scan_id

    mock_visit_package = AsyncMock(side_effect=BaseAppError("RIP"))
    monkeypatch.setattr("src.services.crawler._visit_package", mock_visit_package)

    with pytest.raises(BaseAppError):
        await run_scan(scan_id=scan_id, root_package="test-package")

    # PostgreSQL
    scan_record = await Scan.objects().get(Scan.scan_id == scan_id)
    assert scan_record is not None
    assert scan_record.root_package == "test-package"
    assert scan_record.status == "failed"
    assert scan_record.error_message == "RIP"
    assert scan_record.completed_at is not None
    assert scan_record.total_nodes == 0

    # Neo4j
    scan_node_neo = await ScanNode.nodes.get(scan_id=scan_id)
    assert scan_node_neo is not None
    assert scan_node_neo.root_package == "test-package"
    assert scan_node_neo.status == "failed"
