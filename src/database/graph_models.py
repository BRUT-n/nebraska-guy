from neomodel import (
    AsyncRelationshipTo,
    AsyncStructuredNode,
    AsyncStructuredRel,
    BooleanProperty,
    DateTimeProperty,
    FloatProperty,
    IntegerProperty,
    StringProperty,
)


class ScanNode(AsyncStructuredNode):
    """
    Узел скана в графе.
    """

    __label__ = "Scan"

    scan_id = IntegerProperty(required=True)
    root_package = StringProperty(required=True)
    status = StringProperty(required=True)


class DependsOnRel(AsyncStructuredRel):
    """
    Свойства связи DEPENDS_ON.
    """

    constraint = StringProperty()
    dependency_type = StringProperty()


class PackageNode(AsyncStructuredNode):
    """
    Узел пакета в графе.
    """

    __label__ = "Package"

    scan_id = IntegerProperty(required=True)
    name = StringProperty(required=True)
    ecosystem = StringProperty(required=True)
    version = StringProperty()
    contributors_count = IntegerProperty()
    last_commit_at = DateTimeProperty()
    is_archived = BooleanProperty()
    github_repo_url = StringProperty()
    stars = IntegerProperty()
    bus_factor = IntegerProperty()
    fragility_score = FloatProperty()

    depends_on = AsyncRelationshipTo("PackageNode", "DEPENDS_ON", model=DependsOnRel)
