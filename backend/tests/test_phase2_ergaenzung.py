"""Tests für Wortvervollständigung (Trie), N-Gramm-Lernen und Dispatcher."""

from __future__ import annotations

import pytest

from app import dispatcher
from app.lernen import frequenz, ngramm_speicher, woerterbuch
from app.modelle.ergaenzung import ErgaenzungsAnfrage, ErgaenzungsModus, LernAnfrage
from app.routers.learn import learn


async def test_trie_vervollstaendigt_haeufiges_wort():
    if not frequenz.verfuegbar():
        pytest.skip("Frequenzliste nicht vorhanden")
    antwort = await dispatcher.ergaenze(
        ErgaenzungsAnfrage(text_vor="Das ist ein schoenes Beispi", modus=ErgaenzungsModus.WORT)
    )
    texte = [v.text for v in antwort.vorschlaege]
    assert "el" in texte  # Beispi + el = Beispiel
    assert antwort.engine_status.get("trie") == "ok"


async def test_ngram_lernt_und_sagt_vorher():
    for _ in range(3):
        ngramm_speicher.lerne_text("mit freundlichen Gruessen Marcel", profil_id="standard")
    antwort = await dispatcher.ergaenze(
        ErgaenzungsAnfrage(text_vor="mit freundlichen ", modus=ErgaenzungsModus.PHRASE)
    )
    texte = [v.text.strip() for v in antwort.vorschlaege]
    assert any("Gruessen" in t for t in texte)


async def test_learn_fuegt_unbekanntes_wort_hinzu_und_lernt_ngramme():
    # Einzelwort-Übernahme (kein Leerzeichen) -> kein Embedding-Aufruf, kein Netz.
    antwort = await learn(
        LernAnfrage(
            uebernommen_text="Blupfwort",
            text_vor="Ich schreibe ein ",
            uebernommen_engine="trie",
        )
    )
    assert antwort.gelernt is True
    # 'Blupfwort' ist kein echtes Wort -> wandert ins persönliche Wörterbuch.
    assert "blupfwort" in woerterbuch.bekannte_woerter()
    # N-Gramme wurden gelernt.
    assert ngramm_speicher.anzahl() > 0


async def test_trie_ignoriert_zu_kurzen_praefix():
    antwort = await dispatcher.ergaenze(
        ErgaenzungsAnfrage(text_vor="a", modus=ErgaenzungsModus.WORT)
    )
    assert antwort.vorschlaege == []
