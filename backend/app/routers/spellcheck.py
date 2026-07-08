"""Endpunkt Rechtschreib-/Grammatikprüfung."""

from __future__ import annotations

from fastapi import APIRouter

from app.modelle.pruefung import PruefAnfrage, PruefAntwort
from app.services import pruefung

router = APIRouter(tags=["Prüfung"])


@router.post("/spellcheck")
def spellcheck(anfrage: PruefAnfrage) -> PruefAntwort:
    return pruefung.fuehre_pruefung(anfrage)
