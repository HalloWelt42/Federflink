"""Endpunkt neuronale Ganzsatz-Korrektur."""

from __future__ import annotations

from fastapi import APIRouter

from app import config
from app.fehler import LimitUeberschritten
from app.modelle.pruefung import KorrekturAnfrage, KorrekturAntwort
from app.services import korrektur

router = APIRouter(tags=["Korrektur"])


@router.post("/correct")
async def correct(anfrage: KorrekturAnfrage) -> KorrekturAntwort:
    if len(anfrage.text) > config.MAX_TEXT_ZEICHEN:
        raise LimitUeberschritten(
            f"Text zu lang ({len(anfrage.text)} Zeichen, erlaubt {config.MAX_TEXT_ZEICHEN})."
        )
    return await korrektur.korrigiere(anfrage.text, modell=anfrage.modell)
