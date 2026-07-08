"""Tests fuer die LLM-Ergaenzung: SSE-Fluss, Nachbereitung, Zwei-Ruf-Fallback (gemockt)."""

from __future__ import annotations

from collections.abc import AsyncIterator

from fastapi.testclient import TestClient

from app.ergaenzungs_engines.llm_engine import LlmEngine, nachbereiten
from app.main import app
from app.modelle.ergaenzung import ErgaenzungsAnfrage, ErgaenzungsModus
from app.services import llm_client


def test_nachbereiten_entfernt_reasoning():
    anfrage = ErgaenzungsAnfrage(text_vor="Ich sage ", modus=ErgaenzungsModus.PHRASE)
    v = nachbereiten(anfrage, "<think>kurz ueberlegen</think>hallo Welt")
    assert v is not None and v.text == "hallo Welt"
    # Reines, abgeschnittenes Nachdenken -> kein Vorschlag
    assert nachbereiten(anfrage, "<think>nur nachdenken ohne Ende") is None


def test_nachbereiten_normalisiert_abstaende():
    # Offenes Wort am Ende -> Modellausgabe wird direkt angehaengt (kein Leerzeichen).
    mitten = ErgaenzungsAnfrage(text_vor="Gut", modus=ErgaenzungsModus.WORT)
    assert nachbereiten(mitten, " en").text == "en"  # Gut + en = Guten
    # Trenner steht schon -> fuehrendes Leerzeichen der Ausgabe entfaellt.
    nach_leer = ErgaenzungsAnfrage(text_vor="Guten ", modus=ErgaenzungsModus.WORT)
    assert nachbereiten(nach_leer, " Morgen").text == "Morgen"


async def test_llm_engine_einmalig(monkeypatch):
    async def fake_chat(*args, **kwargs):
        return "guten Tag"

    monkeypatch.setattr(llm_client, "chat", fake_chat)
    res = await LlmEngine().ergaenze(
        ErgaenzungsAnfrage(text_vor="Ich sage ", modus=ErgaenzungsModus.PHRASE), None
    )
    assert res and res[0].text == "guten Tag" and res[0].engine == "llm"


def test_sse_liefert_instant_und_upgrade(monkeypatch):
    async def fake_stream(*args, **kwargs) -> AsyncIterator[str]:
        for delta in ["vielen", " Dank"]:
            yield delta

    monkeypatch.setattr(llm_client, "chat_stream", fake_stream)
    monkeypatch.setattr(llm_client, "zuletzt_erreichbar", lambda: True)

    client = TestClient(app)
    antwort = client.post(
        "/api/complete",
        headers={"Accept": "text/event-stream"},
        json={"text_vor": "Ich schreibe ", "modus": "phrase"},
    )
    koerper = antwort.text
    assert "event: instant" in koerper
    assert "event: upgrade" in koerper
    assert "vielen Dank" in koerper
    assert "event: done" in koerper
