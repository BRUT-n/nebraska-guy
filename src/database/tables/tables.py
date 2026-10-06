from piccolo.columns import BigSerial, Integer, Text, Timestamptz, Varchar
from piccolo.columns.defaults.timestamptz import TimestamptzNow
from piccolo.table import Table


class Scan(Table):
    """
    Запрос на сканирование пакета.
    """

    scan_id = BigSerial(primary_key=True)
    root_package = Varchar(length=255, default=None, null=False)
    root_ecosystem = Varchar(length=50, default=None, null=False)
    status = Varchar(length=20, default=None, null=False)
    total_nodes = Integer(default=0)
    error_message = Text(null=True)
    report = Text(null=True)
    created_at = Timestamptz(default=TimestamptzNow())
    started_at = Timestamptz(null=True, default=None)
    completed_at = Timestamptz(null=True, default=None)
