"""Modelle fuer Rechtschreibpruefung (/spellcheck) und Korrektur (/correct)."""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class BefundArt(StrEnum):
    RECHTSCHREIBUNG = "rechtschreibung"
    GRAMMATIK = "grammatik"
    ZEICHENSETZUNG = "zeichensetzung"
    STIL = "stil"
    TIPPFEHLER = "tippfehler"


class Befund(BaseModel):
    """Ein einzelner Fund in einem Text: Position, Art, Vorschlaege."""

    offset: int = Field(ge=0, description="0-basierter Zeichen-Offset im Text")
    laenge: int = Field(ge=0, description="Laenge der betroffenen Stelle in Zeichen")
    art: BefundArt
    meldung: str = ""
    regel_id: str | None = None
    vorschlaege: list[str] = Field(default_factory=list)
    engine: str = ""


class PruefAnfrage(BaseModel):
    text: str
    sprache: str = "de-DE"
    engines: list[str] | None = Field(
        default=None, description="Leer = alle aktiven Pruef-Engines"
    )


class PruefAntwort(BaseModel):
    befunde: list[Befund]
    engines: list[str] = Field(description="Tatsaechlich ausgefuehrte Engines")
    dauer_ms: int = 0


class KorrekturAnfrage(BaseModel):
    text: str
    profil_id: str | None = None
    modell: str | None = None


class KorrekturAntwort(BaseModel):
    original: str
    korrigiert: str
    engine: str
    veraendert: bool
