"""Test-Konfiguration: lenkt die Datenbank auf eine Wegwerf-Datei im Projekt.

So bleiben Tests im Projektordner und rühren die echte Datenbank nicht an.
Das Wörterbuch-Verzeichnis bleibt das echte (für die Hunspell-/Trie-Tests);
fehlt es, überspringen die betreffenden Tests.
"""

from __future__ import annotations

import os
from pathlib import Path

_ARTEFAKTE = Path(__file__).parent / "artefakte"
_ARTEFAKTE.mkdir(exist_ok=True)
os.environ["FEDERFLINK_DB_PFAD"] = str(_ARTEFAKTE / "test.db")

import pytest  # noqa: E402

from app import registry  # noqa: E402
from app.persistence.db import get_db  # noqa: E402

# Engines registrieren (idempotent), damit der Dispatcher sie kennt.
registry.entdecke_module()


@pytest.fixture(autouse=True)
def frische_db():
    db = get_db()
    db.init_schema()
    with db.connect() as conn:
        conn.execute("DELETE FROM woerter")
        conn.execute("DELETE FROM ngramme")
        conn.execute("DELETE FROM lern_ereignisse")
    yield
