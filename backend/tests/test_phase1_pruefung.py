"""Tests fuer Rechtschreibpruefung, persoenliches Woerterbuch und Korrektur-Schutznetze."""

from __future__ import annotations

import pytest

from app.lernen import woerterbuch
from app.modelle.pruefung import PruefAnfrage
from app.pruef_engines.hunspell_engine import HunspellEngine
from app.services import korrektur, llm_client, pruefung


def _hunspell_da() -> bool:
    return HunspellEngine().ist_verfuegbar()


def test_hunspell_findet_fehler_und_schlaegt_vor():
    if not _hunspell_da():
        pytest.skip("Deutsches Woerterbuch nicht vorhanden (tools/hole_woerterbuch.py)")
    text = "Das ist ein Fehlar."
    befunde = HunspellEngine().pruefe(text, "de-DE")
    treffer = [b for b in befunde if text[b.offset : b.offset + b.laenge] == "Fehlar"]
    assert treffer, "Fehlar sollte als Fehler erkannt werden"
    assert "Fehler" in treffer[0].vorschlaege


def test_woerterbuch_filtert_bekanntes_wort():
    if not _hunspell_da():
        pytest.skip("Deutsches Woerterbuch nicht vorhanden")
    text = "Das Wort Xyzzyx kennt niemand."
    vorher = pruefung.fuehre_pruefung(PruefAnfrage(text=text))
    assert any(text[b.offset : b.offset + b.laenge] == "Xyzzyx" for b in vorher.befunde)

    woerterbuch.hinzufuegen("Xyzzyx")
    nachher = pruefung.fuehre_pruefung(PruefAnfrage(text=text))
    assert not any(text[b.offset : b.offset + b.laenge] == "Xyzzyx" for b in nachher.befunde)


def test_woerterbuch_hinzufuegen_und_entfernen():
    woerterbuch.hinzufuegen("Blickfangwort")
    assert "blickfangwort" in woerterbuch.bekannte_woerter()
    assert woerterbuch.entfernen("Blickfangwort") is True
    assert "blickfangwort" not in woerterbuch.bekannte_woerter()


async def test_korrektur_verwirft_halluzination(monkeypatch):
    async def fake_chat(*args, **kwargs):
        return (
            "Hier ist eine voellig andere, sehr lange Antwort, die nichts mit dem "
            "Eingabetext zu tun hat und deutlich mehr Woerter enthaelt als das Original."
        )

    monkeypatch.setattr(llm_client, "chat", fake_chat)
    original = "ich glab das ergibnis stimt nich ganz bitte prufen"
    ergebnis = await korrektur.korrigiere(original)
    assert ergebnis.korrigiert == original
    assert ergebnis.veraendert is False


async def test_korrektur_uebernimmt_gute_korrektur(monkeypatch):
    async def fake_chat(*args, **kwargs):
        return "Ich glaube, das Ergebnis stimmt nicht ganz, bitte pruefen."

    monkeypatch.setattr(llm_client, "chat", fake_chat)
    ergebnis = await korrektur.korrigiere("ich glaube das ergebnis stimt nich ganz bitte pruefen")
    assert ergebnis.veraendert is True
    assert "Ergebnis" in ergebnis.korrigiert
