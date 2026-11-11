import pytest
from src.database.crud.nodes import (
    create_depends_on_edge,
    create_package_node,
    create_scan_node,
    get_package_node,
    get_scan_node,
    update_package_node,
    update_scan_node_status,
)


@pytest.mark.asyncio(loop_scope="session")
async def test_create_scan_node_success():
    """
    Проверяет успешное создание нода скана в БД.
    """
    created_node = await create_scan_node(scan_id=1, root_package="package", status="pending")

    assert created_node.scan_id == 1
    assert created_node.root_package == "package"
    assert created_node.status == "pending"


@pytest.mark.asyncio(loop_scope="session")
async def test_create_scan_node_but_update(create_test_scan_node):
    """
    Проверяет обновление полей, если нод уже существует.
    """
    updated_node = await create_scan_node(1, "renamed", "new_status")

    assert updated_node.scan_id == 1
    assert updated_node.root_package == "renamed"
    assert updated_node.status == "new_status"


@pytest.mark.asyncio(loop_scope="session")
async def test_get_scan_node_success(create_test_scan_node):
    """
    Проверяет вывод нода по существующему айди.
    """
    node = await get_scan_node(1)

    assert node is not None
    assert node.scan_id == 1
    assert node.root_package == "test-scan-node"
    assert node.status == "test"


@pytest.mark.asyncio(loop_scope="session")
async def test_get_scan_node_not_found():
    """
    Проверка None если нода не существует в БД.
    """
    assert await get_scan_node(1) is None


@pytest.mark.asyncio(loop_scope="session")
async def test_update_scan_node_status_success(create_test_scan_node):
    """
    Проверяет изменение статуса в ноде.
    """
    assert await update_scan_node_status(1, "new_status") is True


@pytest.mark.asyncio(loop_scope="session")
async def test_update_scan_node_status_not_found():
    """
    Проверяет изменение статуса в ноде.
    """
    assert await update_scan_node_status(1, "new_status") is False


@pytest.mark.asyncio(loop_scope="session")
async def test_create_package_node_success(create_test_package_node):
    """
    Проверяет создание нода пакета в БД и обновление если нод уже существует .
    """
    package = create_test_package_node

    assert package.name == "test-package-node"
    assert package.stars == 5
    assert package.contributors_count == 1

    updated_package = await create_package_node(
        scan_id=1, name="new-name", ecosystem="pypi", contributors_count=2
    )

    assert updated_package.name == "new-name"
    assert updated_package.contributors_count == 2


@pytest.mark.asyncio(loop_scope="session")
async def test_get_package_node_success(create_test_package_node):
    """
    Проверяет вывод нода пакета по существующему айди.
    """
    node = await get_package_node(1, "test-package-node", "pypi")

    assert node is not None
    assert node.stars == 5
    assert node.contributors_count == 1


@pytest.mark.asyncio(loop_scope="session")
async def test_get_package_node_not_found():
    """
    Проверка None если нода не существует в БД.
    """
    assert await get_package_node(1, "name", "pypi") is None


@pytest.mark.asyncio(loop_scope="session")
async def test_update_package_node(create_test_package_node):
    """
    Проверяет изменение полей нода по ключам.
    """
    assert await update_package_node(1, "test-package-node", "pypi", bus_factor=55) is True


@pytest.mark.asyncio(loop_scope="session")
async def test_update_package_node_not_found():
    """
    Проверяет изменение статуса в ноде.
    """
    assert await update_package_node(1, "some", "pypi", stars=100) is False


@pytest.mark.asyncio(loop_scope="session")
async def test_create_depends_on_edge():
    """
    Проверка создания связи со свойствами между пакетами.
    Создается два нода -> создается связь со свойствами ->
    -> получает "родителя" из БД уже со связью и свойствами ->
    -> проверяет свойства связи -> проверяет идемпотентность функции.
    """
    parent = await create_package_node(1, "parent", "pypi")
    child = await create_package_node(2, "child", "pypi")

    await create_depends_on_edge(
        parent=parent, child=child, constraint=">=1.0.0", dependency_type="runtime"
    )
    updated_parent = await get_package_node(1, "parent", "pypi")

    # проверяет наличие установленной связи
    edges = await updated_parent.depends_on.all()  # type: ignore[reportAttributeAccessIssue]
    assert len(edges) == 1
    assert edges[0].name == "child"

    # проверяет наличие переданных свойств
    rel_property = await updated_parent.depends_on.relationship(edges[0])  # type: ignore[reportAttributeAccessIssue]
    assert rel_property.constraint == ">=1.0.0"
    assert rel_property.dependency_type == "runtime"

    # проверяет идемпотентность при вызове с одинаковыми аргументами
    await create_depends_on_edge(parent, child, constraint=">=1.0.0", dependency_type="runtime")
    updated_parent = await get_package_node(1, "parent", "pypi")
    edges_after_second_call = await updated_parent.depends_on.all()  # type: ignore[reportAttributeAccessIssue]
    assert len(edges_after_second_call) == 1
