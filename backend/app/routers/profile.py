"""Endpunkte zur Verwaltung der Schreibprofile (im UI bedienbar)."""

from __future__ import annotations

from fastapi import APIRouter

from app.modelle.profil import Profil, ProfilAnlage
from app.modelle.woerterbuch import EntfernErgebnis
from app.profile import dienst

router = APIRouter(tags=["Profile"])


@router.get("/profiles")
def liste() -> list[Profil]:
    return dienst.alle_profile()


@router.post("/profiles")
def anlegen(anlage: ProfilAnlage) -> Profil:
    return dienst.anlegen(anlage)


@router.delete("/profiles/{profil_id}")
def entfernen(profil_id: str) -> EntfernErgebnis:
    return EntfernErgebnis(entfernt=dienst.entfernen(profil_id))


@router.get("/profiles/host")
def profil_fuer_host(host: str) -> dict[str, str | None]:
    """Ordnet einem Host per Muster ein Profil zu (für die Browser-Erweiterung)."""
    return {"profil_id": dienst.host_zu_profil(host)}
