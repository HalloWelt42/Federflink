"""Endpunkte zur Verwaltung des persönlichen Wörterbuchs (im UI bedienbar)."""

from __future__ import annotations

from fastapi import APIRouter

from app.lernen import woerterbuch
from app.modelle.woerterbuch import (
    EntfernErgebnis,
    WoerterbuchListe,
    WortAnlage,
    WortEintrag,
)

router = APIRouter(tags=["Wörterbuch"])


@router.get("/woerterbuch")
def liste(profil_id: str | None = None) -> WoerterbuchListe:
    eintraege = [WortEintrag(**e) for e in woerterbuch.liste(profil_id)]
    return WoerterbuchListe(woerter=eintraege, anzahl=woerterbuch.anzahl())


@router.post("/woerterbuch")
def hinzufuegen(anlage: WortAnlage) -> WortEintrag:
    woerterbuch.hinzufuegen(anlage.wort, profil_id=anlage.profil_id, quelle="manuell")
    return WortEintrag(wort=anlage.wort.strip(), profil_id=anlage.profil_id, quelle="manuell")


@router.delete("/woerterbuch")
def entfernen(anlage: WortAnlage) -> EntfernErgebnis:
    return EntfernErgebnis(entfernt=woerterbuch.entfernen(anlage.wort, anlage.profil_id))
