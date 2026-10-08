from neomodel import (
    AsyncStructuredNode,
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

    scan_id = IntegerProperty(unique_index=True, required=True)
    root_package = StringProperty(required=True)
    status = StringProperty(required=True)


class PackageNode(AsyncStructuredNode):
    """
    Узел пакета в графе.
    """

    __label__ = "Package"

    scan_id = IntegerProperty(required=True)
    name = StringProperty(required=True, index=True)
    ecosystem = StringProperty(required=True)
    version = StringProperty()
    contributors_count = IntegerProperty()
    last_commit_at = DateTimeProperty()
    is_archived = BooleanProperty()
    github_repo_url = StringProperty()
    stars = IntegerProperty()
    bus_factor = IntegerProperty()
    fragility_score = FloatProperty()
