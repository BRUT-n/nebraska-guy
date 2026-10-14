from neomodel import adb


async def install_graph_schema() -> None:
    """
    Применяет ограничения и индексы в графовой БД.
    Необходим т.к. neomodel применяет неидемпотентно.
    """

    # уникальный->(автоиндексация) constraint на Scan.scan_id
    await adb.cypher_query(
        """
        CREATE CONSTRAINT scan_id_unique IF NOT EXISTS
        FOR (s:Scan) REQUIRE s.scan_id IS UNIQUE
        """
    )

    # Композитный уникальный->(автоиндексация) constraint на Package
    await adb.cypher_query(
        """
        CREATE CONSTRAINT package_unique IF NOT EXISTS
        FOR (p:Package) REQUIRE (p.scan_id, p.name, p.ecosystem) IS UNIQUE
        """
    )

    # Индексы для быстрого поиска по базе сканов
    await adb.cypher_query(
        """
        CREATE INDEX scan_status_idx IF NOT EXISTS
        FOR (s:Scan) ON (s.status)
        """
    )

    await adb.cypher_query(
        """
        CREATE INDEX package_scan_id_idx IF NOT EXISTS
        FOR (p:Package) ON (p.scan_id)
        """
    )

    await adb.cypher_query(
        """
        CREATE INDEX package_name_idx IF NOT EXISTS
        FOR (p:Package) ON (p.name)
        """
    )

    await adb.cypher_query(
        """
        CREATE INDEX package_fragility_idx IF NOT EXISTS
        FOR (p:Package) ON (p.fragility_score)
        """
    )
