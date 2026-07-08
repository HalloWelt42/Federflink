"""Grundtypen, die ueberall gebraucht werden: JSON-Wert und einheitliches Fehlermodell."""

from __future__ import annotations

from uuid import UUID, uuid4

from pydantic import BaseModel, Field

type JsonWert = None | bool | int | float | str | list["JsonWert"] | dict[str, "JsonWert"]


class FehlerDetail(BaseModel):
    """Einheitliches Fehlermodell aller Endpunkte."""

    code: str
    meldung: str
    details: dict[str, JsonWert] = Field(default_factory=dict)
    request_id: UUID = Field(default_factory=uuid4)


class FehlerAntwort(BaseModel):
    fehler: FehlerDetail
