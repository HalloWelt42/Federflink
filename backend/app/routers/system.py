"""System-Endpunkte: Health und Capabilities."""

from __future__ import annotations

from fastapi import APIRouter

from app import config, registry
from app.lernen import kontext_speicher, ngramm_speicher, telemetrie, woerterbuch
from app.modelle.system import (
    CapabilitiesAntwort,
    EngineAnnahme,
    HealthAntwort,
    LernStatus,
)

router = APIRouter(tags=["System"])


@router.get("/health")
def health() -> HealthAntwort:
    return HealthAntwort(version=config.APP_VERSION)


@router.get("/capabilities")
async def capabilities() -> CapabilitiesAntwort:
    return await registry.capabilities()


@router.get("/models")
async def models() -> dict[str, object]:
    """Erreichbarkeit des Modell-Servers und gemeldete Modelle."""
    from app.services import llm_client

    return await llm_client.status()


@router.get("/status")
def status() -> LernStatus:
    """Lernstand: Woerter, N-Gramme und Annahmen je Engine (Admin-Transparenz)."""
    annahmen = [
        EngineAnnahme(
            engine=str(z["engine"] or "-"),
            uebernahmen=int(z["uebernahmen"] or 0),
            ablehnungen=int(z["ablehnungen"] or 0),
        )
        for z in telemetrie.zusammenfassung()
    ]
    return LernStatus(
        woerter=woerterbuch.anzahl(),
        ngramme=ngramm_speicher.anzahl(),
        kontext=kontext_speicher.anzahl(),
        annahmen=annahmen,
    )
