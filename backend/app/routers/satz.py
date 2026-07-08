"""Endpunkt Satz-Vorschläge (unlogische/ungünstige Sätze verbessern)."""

from __future__ import annotations

from fastapi import APIRouter

from app import config
from app.fehler import LimitUeberschritten
from app.modelle.pruefung import SatzAnfrage, SatzAntwort
from app.services import satz

router = APIRouter(tags=["Satz-Vorschläge"])


@router.post("/satzvorschlaege")
async def satzvorschlaege(anfrage: SatzAnfrage) -> SatzAntwort:
    if len(anfrage.satz) > config.MAX_TEXT_ZEICHEN:
        raise LimitUeberschritten("Satz zu lang.")
    vs = await satz.vorschlaege(anfrage.satz, profil_id=anfrage.profil_id, modell=anfrage.modell)
    return SatzAntwort(satz=anfrage.satz, vorschlaege=vs)
