"""Vertrag für Prüf-Engines: findet Fehler in einem Text.

Eine Engine je Verfahren (Hunspell, LanguageTool ...), registriert per Dekorator
(siehe app.registry). Prüf-Engines sind synchron und schnell (regelbasiert);
die neuronale Ganzsatz-Korrektur ist ein eigener Dienst (app.services.korrektur),
kein Prüf-Engine, weil sie umschreibt statt zu markieren.
"""

from __future__ import annotations

from typing import ClassVar, Protocol, runtime_checkable

from app.modelle.pruefung import Befund


@runtime_checkable
class PruefEngine(Protocol):
    engine_id: ClassVar[str]
    name: ClassVar[str]
    standard_an: ClassVar[bool]

    def ist_verfuegbar(self) -> bool:
        """False, wenn Abhängigkeiten fehlen (z. B. Wörterbuch, Java)."""
        ...

    def pruefe(self, text: str, sprache: str) -> list[Befund]:
        """Liefert alle Funde. Wirft nicht - bei internem Fehler leere Liste."""
        ...
