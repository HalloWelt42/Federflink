"""System-Endpunkte: Health und Capabilities."""

from __future__ import annotations

from fastapi import APIRouter

from app import config, registry
from app.modelle.system import CapabilitiesAntwort, HealthAntwort

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
