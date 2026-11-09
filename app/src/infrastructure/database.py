import os
import sqlite3
from contextlib import contextmanager
from typing import Generator
from src.core.config import settings

def init_db_dir():
    """Asegura que el directorio del archivo de base de datos exista con fallback si no hay permisos."""
    db_dir = os.path.dirname(settings.DATABASE_PATH)
    if db_dir and not os.path.exists(db_dir):
        try:
            os.makedirs(db_dir, exist_ok=True)
        except OSError:
            # Fallback a directorio local ./data o /tmp para pruebas fuera del contenedor
            fallback_dir = os.path.abspath("./data")
            os.makedirs(fallback_dir, exist_ok=True)
            settings.DATABASE_PATH = os.path.join(fallback_dir, "marea_dulce.db")

def get_raw_connection() -> sqlite3.Connection:
    """Crea una conexión directa a SQLite con pragmas optimizados para WAL."""
    init_db_dir()
    conn = sqlite3.connect(
        settings.DATABASE_PATH,
        timeout=10.0,
        isolation_level=None  # Modo autocommit; control manual con BEGIN/COMMIT
    )
    conn.row_factory = sqlite3.Row
    # Activar WAL mode, claves foráneas y busy timeout
    conn.execute("PRAGMA journal_mode = WAL;")
    conn.execute("PRAGMA synchronous = NORMAL;")
    conn.execute("PRAGMA foreign_keys = ON;")
    conn.execute("PRAGMA busy_timeout = 10000;")
    return conn

@contextmanager
def get_db_connection() -> Generator[sqlite3.Connection, None, None]:
    """Generador de contexto para conexiones seguras a SQLite."""
    conn = get_raw_connection()
    try:
        yield conn
    finally:
        conn.close()

@contextmanager
def transaction(conn: sqlite3.Connection, immediate: bool = False):
    """Context manager para transacciones atómicas seguras en SQLite."""
    if immediate:
        conn.execute("BEGIN IMMEDIATE;")
    else:
        conn.execute("BEGIN;")
    try:
        yield
        conn.execute("COMMIT;")
    except Exception:
        conn.execute("ROLLBACK;")
        raise
