"""Modelle fuer die Verwaltung des persoenlichen Woerterbuchs."""

from __future__ import annotations

from pydantic import BaseModel


class WortEintrag(BaseModel):
    wort: str
    profil_id: str = "standard"
    haeufigkeit: int = 1
    quelle: str = "manuell"


class WortAnlage(BaseModel):
    wort: str
    profil_id: str = "standard"


class WoerterbuchListe(BaseModel):
    woerter: list[WortEintrag]
    anzahl: int


class EntfernErgebnis(BaseModel):
    entfernt: bool
