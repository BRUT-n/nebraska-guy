from neomodel import adb

from src.database.graph_models import PackageNode, ScanNode


async def install_graph_schema() -> None:
    """
    Применяет все constraints и indexes из моделей + композитный constraint
    """
    # Стандартные labels из моделей (unique_index, index
    await adb.install_labels(ScanNode)
    await adb.install_labels(PackageNode)

    # Композитный уникальный constraint (не поддерживается через модели)
    await adb.cypher_query(
        """
        CREATE CONSTRAINT package_unique IF NOT EXISTS
        FOR (p:Package) REQUIRE (p.scan_id, p.name, p.ecosystem) IS UNIQUE
        """
    )

    # Дополнительные индексы, которые не описаны в моделях
    await adb.cypher_query(
        """
        CREATE INDEX scan_status_idx IF NOT EXISTS
        FOR (s:Scan) ON (s.status)
        """
    )

    await adb.cypher_query(
        """
        CREATE INDEX package_fragility_idx IF NOT EXISTS
        FOR (p:Package) ON (p.fragility_score)
        """
    )
