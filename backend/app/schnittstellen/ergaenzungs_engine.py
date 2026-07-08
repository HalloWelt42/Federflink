"""Vertrag für Ergänzungs-Engines: schlägt eine Fortsetzung am Cursor vor.

Schnelle Engines (Trie, N-Gramm) antworten praktisch sofort; die LLM-Engine ist
langsamer, aber kontextsensitiv. Der Dispatcher (app.dispatcher) führt sie
gemeinsam aus und mischt die Ergebnisse (Instant-Vorschlag zuerst, LLM-Upgrade
danach). Alle Methoden sind async, damit der Dispatcher einheitlich bleibt.
"""

from __future__ import annotations

from typing import ClassVar, Protocol, runtime_checkable

from app.modelle.ergaenzung import ErgaenzungsAnfrage, Vorschlag


@runtime_checkable
class ErgaenzungsEngine(Protocol):
    engine_id: ClassVar[str]
    name: ClassVar[str]
    standard_an: ClassVar[bool]
    streaming: ClassVar[bool]

    def ist_verfuegbar(self) -> bool:
        """False, wenn Voraussetzungen fehlen (z. B. LLM nicht erreichbar)."""
        ...

    async def ergaenze(self, anfrage: ErgaenzungsAnfrage, kontext: str | None) -> list[Vorschlag]:
        """Liefert bewertete Vorschläge. `kontext` ist optionaler Umfeld-Kontext
        (aus dem Retrieval), den kontextsensitive Engines nutzen können."""
        ...
