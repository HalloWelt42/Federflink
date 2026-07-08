"""Tests für Satz-Vorschläge (unlogische Sätze), LLM gemockt."""

from __future__ import annotations

from app.services import llm_client, satz
from app.services.satz import _parse


def test_parse_json_array():
    assert _parse('["Variante eins", "Variante zwei"]') == ["Variante eins", "Variante zwei"]


def test_parse_entfernt_reasoning_und_liste():
    roh = "<think>kurz nachdenken</think>\n1. Erste Variante\n2. Zweite Variante"
    assert _parse(roh) == ["Erste Variante", "Zweite Variante"]


async def test_vorschlaege_filtert_und_begrenzt(monkeypatch):
    async def fake_chat(*args, **kwargs):
        return (
            '["Der Hund bellt laut.", "Der Hund bellt laut.", '
            '"Der Hund bellt sehr laut.", "Der Hund bellt draußen.", "Vierte Variante"]'
        )

    monkeypatch.setattr(llm_client, "chat", fake_chat)
    vs = await satz.vorschlaege("Der Hund bellt laut.")
    assert "Der Hund bellt laut." not in vs  # Eingabe entfernt
    assert len(vs) <= 3  # hoechstens drei
    assert "Der Hund bellt sehr laut." in vs
    assert len(vs) == len(set(vs))  # keine Duplikate


async def test_vorschlaege_kurzer_satz_leer():
    assert await satz.vorschlaege("Hi") == []
