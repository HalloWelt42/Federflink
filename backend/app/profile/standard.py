"""Eingebaute Schreibprofile.

Ein Profil buendelt Ton/Stil, ein eigenes Woerterbuch und (ab Phase 4) einen
eigenen Umfeld-Kontext. Diese Vorgaben lassen sich im UI erweitern und aendern;
sie sind nur der Startbestand, nichts ist fest verdrahtet.
"""

from __future__ import annotations

from app.modelle.system import ProfilInfo

STANDARD_PROFILE: tuple[ProfilInfo, ...] = (
    ProfilInfo(
        id="standard",
        name="Standard",
        sprache="de",
        beschreibung="Allgemeines Schreiben ohne besonderen Ton.",
    ),
    ProfilInfo(
        id="email-de",
        name="E-Mail (foermlich)",
        sprache="de",
        beschreibung="Hoefliche, foermliche Korrespondenz.",
    ),
    ProfilInfo(
        id="chat-de",
        name="Chat (locker)",
        sprache="de",
        beschreibung="Kurze, lockere Nachrichten.",
    ),
)


def standard_profile() -> list[ProfilInfo]:
    return list(STANDARD_PROFILE)
