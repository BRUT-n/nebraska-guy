import os

from dotenv import load_dotenv
from piccolo.conf.apps import AppRegistry
from piccolo.engine.postgres import PostgresEngine

load_dotenv()

DB = PostgresEngine(
    config={
        "database": os.environ["POSTGRES_DB"],
        "user": os.environ["POSTGRES_USER"],
        "password": os.environ["POSTGRES_PASSWORD"],
        "host": os.environ.get("POSTGRES_HOST", "localhost"),
        "port": int(os.environ.get("POSTGRES_PORT", 5432)),
    }
)

APP_REGISTRY = AppRegistry(apps=["src.database.tables.piccolo_app"])
