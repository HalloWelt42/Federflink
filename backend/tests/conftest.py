"""Test-Konfiguration: lenkt die Datenbank auf eine Wegwerf-Datei im Projekt.

So bleiben Tests im Projektordner und ruehren die echte Datenbank nicht an.
Das Woerterbuch-Verzeichnis bleibt das echte (fuer die Hunspell-Tests); fehlt es,
ueberspringen die betreffenden Tests.
"""

from __future__ import annotations

import os
from pathlib import Path

_ARTEFAKTE = Path(__file__).parent / "artefakte"
_ARTEFAKTE.mkdir(exist_ok=True)
os.environ["FEDERFLINK_DB_PFAD"] = str(_ARTEFAKTE / "test.db")
