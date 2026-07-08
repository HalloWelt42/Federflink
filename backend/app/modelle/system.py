"""Modelle fuer System-Endpunkte: Health und Capabilities.

Capabilities ist der Selbstauskunfts-Endpunkt: Frontend und Browser-Erweiterung
lesen hier, welche Engines, Modi, Profile und Grenzen der Server anbietet, und
bauen ihre Bedienelemente daraus - nichts ist im Client fest verdrahtet.
"""

from __future__ import annotations

from pydantic import BaseModel, Field


class HealthAntwort(BaseModel):
    status: str = "ok"
    name: str = "Federflink"
    version: str


class EngineInfo(BaseModel):
    id: str
    name: str
    aktiv: bool = Field(description="Engine ist einsatzbereit (Abhaengigkeiten vorhanden)")
    standard_an: bool = Field(description="Ist die Engine per Vorgabe eingeschaltet")
    streaming: bool = False


class ProfilInfo(BaseModel):
    id: str
    name: str
    sprache: str = "de"
    beschreibung: str = ""


class Grenzen(BaseModel):
    budget_vor: int
    budget_nach: int
    debounce_ms: int
    min_zeichen: int
    max_vorschlaege: int
    max_text_zeichen: int


class LlmStatus(BaseModel):
    erreichbar: bool
    url: str
    modelle: list[str] = Field(default_factory=list)


class EngineAnnahme(BaseModel):
    engine: str
    uebernahmen: int
    ablehnungen: int


class LernStatus(BaseModel):
    woerter: int
    ngramme: int
    annahmen: list[EngineAnnahme]


class CapabilitiesAntwort(BaseModel):
    version: str
    name: str = "Federflink"
    pruef_engines: list[EngineInfo]
    ergaenzungs_engines: list[EngineInfo]
    modi: list[str]
    profile: list[ProfilInfo]
    grenzen: Grenzen
    funktionen: dict[str, bool] = Field(default_factory=dict)
    llm: LlmStatus | None = None
