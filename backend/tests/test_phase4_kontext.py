"""Tests fuer Schreibprofile und den Umfeld-Kontextspeicher (Embeddings gemockt)."""

from __future__ import annotations

import pytest

from app.lernen import kontext_speicher
from app.modelle.profil import ProfilAnlage
from app.profile import dienst
from app.services import llm_client


@pytest.fixture(autouse=True)
def _leere_profile_und_kontext():
    from app.persistence.db import get_db

    with get_db().connect() as conn:
        conn.execute("DELETE FROM profile")
        conn.execute("DELETE FROM kontext_passagen")
    yield


def test_eingebaute_profile_vorhanden():
    ids = {p.id for p in dienst.alle_profile()}
    assert {"standard", "email-de", "chat-de"} <= ids


def test_profil_anlegen_und_entfernen():
    dienst.anlegen(ProfilAnlage(id="notiz", name="Notizen", stil_prompt="knapp"))
    assert dienst.hole_profil("notiz") is not None
    assert dienst.stil_prompt("notiz") == "knapp"
    assert dienst.entfernen("notiz") is True
    assert dienst.hole_profil("notiz") is None


def test_eingebautes_profil_nicht_loeschbar():
    assert dienst.entfernen("standard") is False


def test_host_zuordnung():
    dienst.anlegen(ProfilAnlage(id="firma", name="Firma", host_muster=["*.example.org"]))
    assert dienst.host_zu_profil("mail.example.org") == "firma"
    assert dienst.host_zu_profil("anderer.host") is None


async def test_kontext_merken_und_finden(monkeypatch):
    async def fake_embed(texte, **kwargs):
        vektoren = []
        for t in texte:
            tl = t.lower()
            if "apfel" in tl:
                vektoren.append([1.0, 0.0, 0.0])
            elif "auto" in tl:
                vektoren.append([0.0, 1.0, 0.0])
            else:
                vektoren.append([0.0, 0.0, 1.0])
        return vektoren, "mock", 3

    monkeypatch.setattr(llm_client, "embed", fake_embed)

    assert await kontext_speicher.merke_passage("Der Apfel ist rot und suess")
    assert await kontext_speicher.merke_passage("Das Auto faehrt sehr schnell")
    assert kontext_speicher.anzahl() == 2

    treffer = await kontext_speicher.aehnliche("Ich mag frischen Apfelsaft", top=1)
    assert treffer and "Apfel" in treffer[0]
