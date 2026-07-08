"""Eingebaute Schreibprofile (Startbestand).

Ein Profil bündelt Ton/Stil (Stilhinweis für die LLM-Ergänzung), ein eigenes
Wörterbuch/N-Gramm und einen eigenen Umfeld-Kontext. Host-Muster bleiben leer -
Zuordnungen legt der Nutzer selbst fest (nichts fest verdrahten, keine fremden
Marken als Vorgabe). Weitere Profile lassen sich im UI anlegen.
"""

from __future__ import annotations

from app.modelle.profil import Profil

EINGEBAUTE: tuple[Profil, ...] = (
    Profil(
        id="standard",
        name="Standard",
        beschreibung="Allgemeines Schreiben ohne besonderen Ton.",
        stil_prompt="",
        eingebaut=True,
    ),
    Profil(
        id="email-de",
        name="E-Mail (förmlich)",
        beschreibung="Höfliche, förmliche Korrespondenz.",
        stil_prompt="Schreibe höflich und förmlich, sieze die Leser, klar und knapp.",
        eingebaut=True,
    ),
    Profil(
        id="chat-de",
        name="Chat (locker)",
        beschreibung="Kurze, lockere Nachrichten.",
        stil_prompt="Schreibe locker, kurz und freundlich, wie in einer Chat-Nachricht.",
        eingebaut=True,
    ),
)
