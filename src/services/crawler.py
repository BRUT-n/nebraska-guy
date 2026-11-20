import json
import logging
from dataclasses import dataclass, field

from src.clients.github import fetch_repo_info_for_node
from src.clients.pypi import get_package
from src.database.crud.nodes import (
    create_depends_on_edge,
    create_includes_edge,
    create_package_node,
    create_scan_node,
    get_package_node,
    update_scan_node_status,
)
from src.database.crud.scans import finalize_scan, update_scan_status
from src.database.graph_models import PackageNode
from src.exceptions import BaseAppError, PackageNotFoundError, PyPIClientError
from src.models.requirement import ParsedDependency
from src.services.dependency_parser import parse_requirements
from src.services.github_link import extract_github_repo

DEFAULT_MAX_DEPTH = 10
DEFAULT_MAX_NODES = 1000

logger = logging.getLogger(__name__)


@dataclass
class CrawlContext:
    """
    Настройки и счетчики текущего обхода, общие для всех шагов рекурсии.
    """

    scan_id: int
    max_depth: int = DEFAULT_MAX_DEPTH
    max_nodes: int = DEFAULT_MAX_NODES
    nodes_count: int = 0
    failed_packages: list[str] = field(default_factory=list)


async def _get_or_create_package_node(
    ctx: CrawlContext,
    package_name: str,
) -> tuple[PackageNode | None, list[ParsedDependency]]:
    """
    Возвращает узел пакета из БД и список его зависимостей (если пакет скачан впервые).
    """
    existing_package_node = await get_package_node(ctx.scan_id, package_name, "pypi")
    if existing_package_node is not None:
        return existing_package_node, []

    # получения информации от PyPI
    try:
        info = await get_package(package_name)
    except (PackageNotFoundError, PyPIClientError) as exc:
        logger.warning("PyPI failed for %s: %s", package_name, exc)
        ctx.failed_packages.append(package_name)
        return None, []

    # получение полей с github
    github_fields = {}
    owner_repo = extract_github_repo(info)
    if owner_repo is not None:
        github_fields = await fetch_repo_info_for_node(*owner_repo)

    # создание узла с полученными данными
    new_node = await create_package_node(
        scan_id=ctx.scan_id,
        name=package_name,
        ecosystem="pypi",
        version=info.version,
        **github_fields,
    )
    ctx.nodes_count += 1

    # получение зависимостей
    deps = parse_requirements(info.requires_dist)

    return new_node, deps


async def _visit_package(
    ctx: CrawlContext,
    package_name: str,
    parent_node: PackageNode | None,
    depth: int,
    constraint: str | None,
    dependency_type: str,
) -> PackageNode | None:
    """
    Обходит один пакет: находит его или создает, связывает с родителем и идет вглубь зависимостей.
    """
    # проверяет лимиты нодов
    if ctx.nodes_count >= ctx.max_nodes:
        logger.warning("max_nodes=%d reached at %s", ctx.max_nodes, package_name)
        return None

    # поиск или создание пакета с зависимостями в БД
    node, deps = await _get_or_create_package_node(ctx, package_name)
    if node is None:
        return None

    # если пакет не корневой (есть родитель) строится связь от родителя к пакету
    if parent_node is not None:
        await create_depends_on_edge(
            parent=parent_node,
            child=node,
            constraint=constraint,
            dependency_type=dependency_type,
        )

    # рекурсивный обход дочерних зависимости если в рамках лимита
    if depth < ctx.max_depth:
        for dep in deps:
            await _visit_package(
                ctx=ctx,
                package_name=dep.name,
                parent_node=node,
                depth=depth + 1,
                constraint=dep.version_spec,
                dependency_type=dep.dependency_type.value,
            )

    return node


async def run_scan(
    scan_id: int,
    root_package: str,
    max_depth: int = DEFAULT_MAX_DEPTH,
    max_nodes: int = DEFAULT_MAX_NODES,
) -> CrawlContext:
    """
    Запускает обход по пакетам. Финализирует скан.
    """
    ctx = CrawlContext(scan_id, max_depth, max_nodes)

    # записывает запущенный статус в двух БД
    await update_scan_status(scan_id=scan_id, new_status="running")
    scan_node = await create_scan_node(scan_id=scan_id, root_package=root_package, status="running")

    try:
        root_package_node = await _visit_package(
            ctx=ctx,
            package_name=root_package,
            parent_node=None,
            depth=0,
            constraint=None,
            dependency_type="runtime",
        )

        if root_package_node is not None:
            await create_includes_edge(scan_node, root_package_node)

        # вычисление финального статуса
        if ctx.failed_packages:
            final_status = "partial"
            error_message = json.dumps({"failed_packages": ctx.failed_packages})
        else:
            final_status = "completed"
            error_message = None

        await finalize_scan(scan_id, final_status, ctx.nodes_count, error_message)
        await update_scan_node_status(scan_id, final_status)

    except BaseAppError as exc:
        logger.exception("Scan %s failed: %s", scan_id, exc)
        await finalize_scan(scan_id, "failed", ctx.nodes_count, str(exc))
        await update_scan_node_status(scan_id, "failed")
        raise
    return ctx
