"""Endpunkt Textergaenzung (Instant-Pfad, nicht streamend).

Der streamende Pfad mit LLM-Upgrade (SSE) kommt in Phase 3 hinzu.
"""

from __future__ import annotations

from fastapi import APIRouter

from app import config, dispatcher
from app.fehler import LimitUeberschritten
from app.modelle.ergaenzung import ErgaenzungsAnfrage, ErgaenzungsAntwort

router = APIRouter(tags=["Ergaenzung"])


@router.post("/complete")
async def complete(anfrage: ErgaenzungsAnfrage) -> ErgaenzungsAntwort:
    if len(anfrage.text_vor) > config.MAX_TEXT_ZEICHEN:
        raise LimitUeberschritten("Kontext zu lang.")
    return await dispatcher.ergaenze(anfrage)
