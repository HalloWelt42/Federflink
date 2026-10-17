"""Die Fassungsabfrage liest version.json frisch, damit offene Oberflächen eine neue Fassung bemerken."""

from __future__ import annotations

from pathlib import Path

from app import config
from app.routers import system

_ARTEFAKTE = Path(__file__).parent / "artefakte"


def test_health_liest_version_frisch(monkeypatch):
    datei = _ARTEFAKTE / "version.json"
    datei.write_text('{"version": "9.9.9"}', encoding="utf-8")
    monkeypatch.setattr(config, "VERSIONSDATEI", datei)
    assert system.health().version == "9.9.9"
    datei.write_text('{"version": "9.9.10"}', encoding="utf-8")
    assert system.health().version == "9.9.10"
