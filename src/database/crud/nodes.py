from src.database.graph_models import PackageNode, ScanNode


async def create_scan_node(
    scan_id: int,
    root_package: str,
    status: str,
) -> ScanNode:
    """
    Найти или создать скан. При повторном вызове — обновить.
    """
    node = await ScanNode.nodes.get_or_none(scan_id=scan_id)
    if node is None:
        node = ScanNode(
            scan_id=scan_id,
            root_package=root_package,
            status=status,
        )
    else:
        node.root_package = root_package  # type: ignore[reportAttributeAccessIssue]
        node.status = status  # type: ignore[reportAttributeAccessIssue]

    await node.save()
    return node


async def get_scan_node(scan_id: int) -> ScanNode | None:
    """
    Возвращает узел Scan или None.
    """
    return await ScanNode.nodes.get_or_none(scan_id=scan_id)


async def update_scan_node_status(scan_id: int, status: str) -> bool:
    """
    Меняет статус скана на указанный.
    """
    scan_node = await ScanNode.nodes.get_or_none(scan_id=scan_id)
    if scan_node is None:
        return False
    scan_node.status = status  # type: ignore[reportAttributeAccessIssue]
    await scan_node.save()
    return True


async def create_package_node(
    scan_id: int,
    name: str,
    ecosystem: str,
    **fields,
) -> PackageNode:
    """Найти пакет по (scan_id, name, ecosystem). Если нет — создать. Если есть — обновить."""
    existing = await PackageNode.nodes.get_or_none(
        scan_id=scan_id,
        name=name,
        ecosystem=ecosystem,
    )
    if existing is not None:
        for key, value in fields.items():
            if value is not None:
                setattr(existing, key, value)
        await existing.save()
        return existing

    node = await PackageNode(
        scan_id=scan_id,
        name=name,
        ecosystem=ecosystem,
        **fields,
    ).save()
    return node


async def get_package_node(
    scan_id: int,
    name: str,
    ecosystem: str,
) -> PackageNode | None:
    """
    Возвращает узел Package или None. Используется для защиты от циклов.
    Будет использоваться краулером.
    """
    return await PackageNode.nodes.get_or_none(scan_id=scan_id, name=name, ecosystem=ecosystem)


async def update_package_node(
    scan_id: int,
    name: str,
    ecosystem: str,
    **fields,
) -> bool:
    """
    Обновляет поля узла Package. Возвращает True, если узел найден
    """
    node = await get_package_node(scan_id, name, ecosystem)
    if node is None:
        return False
    for key, value in fields.items():
        setattr(node, key, value)
    await node.save()
    return True


async def create_depends_on_edge(
    parent: PackageNode,
    child: PackageNode,
    constraint: str | None,
    dependency_type: str,
) -> None:
    """
    Создаёт связь DEPENDS_ON со свойствами версии и типа зависимости. Идемпотентно.
    """
    properties = {"constraint": constraint, "dependency_type": dependency_type}
    await parent.depends_on.connect(child, properties=properties)  # type: ignore[reportAttributeAccessIssue]
