"""Modelle für die Textergänzung (/complete) und das Lernsignal (/learn).

Die JSON-Schlüssel sind bewusst deutsch und ASCII gehalten; sie bilden den
stabilen Vertrag zwischen Server, Browser-Erweiterung und künftigen Clients
(siehe docs/02_API.md).
"""

from __future__ import annotations

from enum import StrEnum

from pydantic import BaseModel, Field


class ErgaenzungsModus(StrEnum):
    WORT = "wort"
    PHRASE = "phrase"
    SATZ = "satz"


class Cursorlage(BaseModel):
    im_wort: bool = False
    am_zeilenende: bool = True


class SeitenKontext(BaseModel):
    """Herkunfts-Metadaten des Feldes (für Profilwahl und Telemetrie)."""

    host: str = ""
    feld_art: str = ""  # input | textarea | contenteditable
    sprach_hinweis: str = "de"


class ErgaenzungsAnfrage(BaseModel):
    protokoll: int = 1
    request_id: str = ""
    sitzung_id: str = ""
    text_vor: str = Field(default="", description="Text bis zum Cursor")
    text_nach: str = Field(default="", description="Text nach dem Cursor")
    cursor: Cursorlage = Field(default_factory=Cursorlage)
    modus: ErgaenzungsModus = ErgaenzungsModus.PHRASE
    engines: list[str] | None = Field(default=None, description="Leer = alle aktiven Engines")
    profil_id: str | None = None
    seite: SeitenKontext = Field(default_factory=SeitenKontext)
    locale: str = "de-DE"
    max_vorschlaege: int = 3
    kontext_hash: str = ""


class Vorschlag(BaseModel):
    id: str
    text: str
    engine: str
    score: float = 0.0
    art: ErgaenzungsModus = ErgaenzungsModus.PHRASE
    ersetze_vor: int = Field(
        default=0, description="Zeichen vor dem Cursor, die der Vorschlag ersetzt (Autokorrektur)"
    )
    anzeige_text: str | None = None
    final: bool = True


class ErgaenzungsAntwort(BaseModel):
    request_id: str = ""
    erzeugt_ms: int = 0
    vorschlaege: list[Vorschlag] = Field(default_factory=list)
    upgrade_aussteht: bool = False
    engine_status: dict[str, str] = Field(default_factory=dict)


class LernAnfrage(BaseModel):
    """Signal bei Übernahme eines Vorschlags (oder abgelehntem Vorschlag)."""

    request_id: str = ""
    sitzung_id: str = ""
    uebernommen_text: str = ""
    uebernommen_engine: str = ""
    teil_uebernahme: bool = False
    profil_id: str | None = None
    seite: SeitenKontext = Field(default_factory=SeitenKontext)
    # Nur gesetzt, wenn pro Seite "hier verbessern" aktiv ist (Datenschutz-Gate im Client).
    text_vor: str | None = None


class LernAntwort(BaseModel):
    gelernt: bool
    hinweis: str = ""
