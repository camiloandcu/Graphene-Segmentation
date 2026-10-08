"""Transactional local metadata upgrades; no optional model imports."""
import sqlite3


def add_model_registry(connection: sqlite3.Connection) -> None:
    connection.execute("""CREATE TABLE models (
        model_id TEXT PRIMARY KEY, artifact_id TEXT NOT NULL UNIQUE REFERENCES artifacts(id),
        bundle_sha256 TEXT NOT NULL, model_sha256 TEXT NOT NULL,
        name TEXT NOT NULL, version TEXT NOT NULL, imported_at TEXT NOT NULL,
        documents TEXT NOT NULL
    )""")
    connection.execute("""CREATE TABLE model_selection (
        singleton INTEGER PRIMARY KEY CHECK(singleton=1),
        model_id TEXT REFERENCES models(model_id)
    )""")
    connection.execute("INSERT INTO model_selection(singleton,model_id) VALUES(1,NULL)")
