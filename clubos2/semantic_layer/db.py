from __future__ import annotations

import os
from collections.abc import Generator
from contextlib import contextmanager
from pathlib import Path

from sqlalchemy import Engine, create_engine, text
from sqlalchemy.orm import Session, sessionmaker

_repo_root = Path(__file__).resolve().parent.parent.parent
_default_db_path = _repo_root / "var" / "clubos_semantic.duckdb"
DATABASE_URL = os.getenv("DATABASE_URL", f"duckdb:///{_default_db_path}")


def get_engine(database_url: str | None = None) -> Engine:
    """Creates a SQLAlchemy engine for the specified database URL.

    Ensures that the directory structure is created for relative file-based databases.
    """
    url = database_url or DATABASE_URL

    # Ensure parent directory exists for file-based DuckDB or SQLite URLs
    if url.startswith("duckdb:///") or url.startswith("sqlite:///"):
        protocol = "duckdb:///" if url.startswith("duckdb:///") else "sqlite:///"
        db_path = url[len(protocol) :]

        if db_path.startswith("/"):
            if db_path.startswith("/./"):
                db_path = db_path[1:]
            elif not os.path.isabs(db_path):
                db_path = db_path.lstrip("/")

        dir_name = os.path.dirname(db_path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)

    return create_engine(url)


# Module-level defaults for local database
_default_engine = get_engine()
_SessionFactory = sessionmaker(bind=_default_engine)


@contextmanager
def get_session(database_url: str | None = None) -> Generator[Session, None, None]:
    """A context manager that yields a SQLAlchemy Session.

    Commits on successful completion, and rolls back on exception.
    """
    if database_url is not None:
        engine = get_engine(database_url)
        factory = sessionmaker(bind=engine)
        session = factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()
    else:
        session = _SessionFactory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()


def bootstrap_db(database_url: str | None = None) -> None:
    """Executes SQL migrations to bootstrap the metric_registry table.

    Runs idempotently using CREATE TABLE IF NOT EXISTS.
    """
    current_dir = os.path.dirname(os.path.abspath(__file__))
    migration_path = os.path.join(current_dir, "migrations", "001_create_metric_registry.sql")

    with open(migration_path, encoding="utf-8") as f:
        sql = f.read()

    engine = get_engine(database_url) if database_url else _default_engine
    with engine.begin() as conn:
        statements = [stmt.strip() for stmt in sql.split(";") if stmt.strip()]
        for stmt in statements:
            conn.execute(text(stmt))
