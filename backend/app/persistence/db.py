"""SQLite-Verbindungsverwaltung und Schema-Initialisierung.

Die Database-Klasse kapselt den Pfad zur SQLite-Datei und liefert frische
Verbindungen via Kontext-Manager. Fremdschluessel-Checks, WAL-Journal und
Busy-Timeout werden bei jeder Verbindung gesetzt (WAL fuer bessere
Nebenlaeufigkeit von Lese-/Lernschreib-Anfragen auf lokalem Dateisystem).
"""

from __future__ import annotations

import sqlite3
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

from app import config

from .schema import MIGRATIONS, SCHEMA_SQL


class Database:
    def __init__(self, db_path: Path | str) -> None:
        self._path = Path(db_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)

    @property
    def path(self) -> Path:
        return self._path

    @contextmanager
    def connect(self) -> Iterator[sqlite3.Connection]:
        """Oeffnet eine Verbindung; committet bei Erfolg, rollback bei Fehler."""
        conn = sqlite3.connect(str(self._path), check_same_thread=False, timeout=5.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        conn.execute("PRAGMA busy_timeout = 5000")
        try:
            yield conn
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            conn.close()

    def init_schema(self) -> None:
        """Erzeugt alle Tabellen und Indizes (idempotent) und migriert Altbestand."""
        with self.connect() as conn:
            conn.executescript(SCHEMA_SQL)
            _wende_migrationen_an(conn)


def _wende_migrationen_an(conn: sqlite3.Connection) -> None:
    for tabelle, spalte, alter_sql in MIGRATIONS:
        vorhandene = {row["name"] for row in conn.execute(f"PRAGMA table_info({tabelle})").fetchall()}
        if spalte not in vorhandene:
            conn.execute(alter_sql)


_db: Database | None = None


def get_db() -> Database:
    """Modul-Singleton der Datenbank am konfigurierten Pfad."""
    global _db
    if _db is None:
        _db = Database(config.DB_PFAD)
    return _db
