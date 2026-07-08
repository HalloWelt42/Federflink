"""Modelle für Schreibprofile."""

from __future__ import annotations

from pydantic import BaseModel, Field


class Profil(BaseModel):
    id: str
    name: str
    sprache: str = "de"
    beschreibung: str = ""
    stil_prompt: str = Field(default="", description="Stilhinweis für die LLM-Ergänzung")
    host_muster: list[str] = Field(default_factory=list, description="Host-Muster -> dieses Profil")
    aktiv: bool = True
    eingebaut: bool = False


class ProfilAnlage(BaseModel):
    id: str
    name: str
    sprache: str = "de"
    beschreibung: str = ""
    stil_prompt: str = ""
    host_muster: list[str] = Field(default_factory=list)
