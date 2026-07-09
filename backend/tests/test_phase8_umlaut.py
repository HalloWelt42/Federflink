"""Tests fuer die Hunspell-validierte Umlaut-Reparatur und das Lernen."""

from __future__ import annotations

import pytest

from app.lernen import frequenz, umlaut
from app.modelle.ergaenzung import LernAnfrage
from app.pruef_engines.hunspell_engine import HunspellEngine
from app.routers.learn import learn


def _woerterbuch_da() -> bool:
    return HunspellEngine().ist_verfuegbar()


def test_repariert_ascii_umlaute():
    if not _woerterbuch_da():
        pytest.skip("kein Woerterbuch")
    assert umlaut.repariere_wort("fuer") == "für"
    assert umlaut.repariere_wort("muessen") == "müssen"
    assert umlaut.repariere_wort("gruesse") == "grüße"
    assert umlaut.repariere_wort("Pruefung") == "Prüfung"


def test_laesst_echte_woerter_unberuehrt():
    if not _woerterbuch_da():
        pytest.skip("kein Woerterbuch")
    for wort in ("neue", "dass", "Adresse", "aktuell", "Prozess", "Steuer", "muss"):
        assert umlaut.repariere_wort(wort) == wort


def test_frequenz_dedup_entfernt_ascii_dublette():
    d = {"für": 100, "fuer": 5, "über": 80, "ueber": 3, "neue": 50}
    frequenz._entferne_ascii_dubletten(d)
    assert "fuer" not in d and "ueber" not in d
    assert "für" in d and "über" in d and "neue" in d


async def test_learn_speichert_echte_umlaute(monkeypatch):
    if not _woerterbuch_da():
        pytest.skip("kein Woerterbuch")
    from app.lernen import kontext_speicher
    from app.persistence.db import get_db

    async def keine_passage(*args, **kwargs):
        return False

    monkeypatch.setattr(kontext_speicher, "merke_passage", keine_passage)

    await learn(
        LernAnfrage(uebernommen_text="fuer die Pruefung", text_vor="Ich lerne ", uebernommen_engine="llm")
    )
    with get_db().connect() as conn:
        woerter = {r["wort"] for r in conn.execute("SELECT wort FROM ngramme").fetchall()}
    klein = {w.lower() for w in woerter}
    assert "prüfung" in klein  # echt gelernt
    assert "pruefung" not in klein and "fuer" not in klein  # keine ASCII-Umlaute
