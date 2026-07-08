"""Endpunkt Rechtschreib-/Grammatikpruefung."""

from __future__ import annotations

from fastapi import APIRouter

from app.modelle.pruefung import PruefAnfrage, PruefAntwort
from app.services import pruefung

router = APIRouter(tags=["Pruefung"])


@router.post("/spellcheck")
def spellcheck(anfrage: PruefAnfrage) -> PruefAntwort:
    return pruefung.fuehre_pruefung(anfrage)
