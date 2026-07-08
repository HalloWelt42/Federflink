"""Modelle für Rechtschreibprüfung (/spellcheck) und Korrektur (/correct)."""

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
    """Ein einzelner Fund in einem Text: Position, Art, Vorschläge."""

    offset: int = Field(ge=0, description="0-basierter Zeichen-Offset im Text")
    laenge: int = Field(ge=0, description="Länge der betroffenen Stelle in Zeichen")
    art: BefundArt
    meldung: str = ""
    regel_id: str | None = None
    vorschlaege: list[str] = Field(default_factory=list)
    engine: str = ""


class PruefAnfrage(BaseModel):
    text: str
    sprache: str = "de-DE"
    profil_id: str = "standard"
    engines: list[str] | None = Field(
        default=None, description="Leer = alle standardmäßig aktiven Prüf-Engines"
    )


class PruefAntwort(BaseModel):
    befunde: list[Befund]
    engines: list[str] = Field(description="Tatsächlich ausgeführte Engines")
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


class SatzAnfrage(BaseModel):
    """Ein einzelner Satz, der auf Sinn/Wortwahl/Grammatik geprueft werden soll."""

    satz: str
    profil_id: str | None = None
    modell: str | None = None


class SatzAntwort(BaseModel):
    satz: str
    vorschlaege: list[str] = Field(default_factory=list)
