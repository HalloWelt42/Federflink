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
def capabilities() -> CapabilitiesAntwort:
    return registry.capabilities()
