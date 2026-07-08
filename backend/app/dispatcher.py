"""Führt die Ergänzungs-Engines aus und mischt ihre Vorschläge.

Der Instant-Pfad (ergaenze) führt nur die schnellen, nicht-streamenden Engines
(Trie, N-Gramm) aus - er bleibt auch dann schnell, wenn später eine langsame
LLM-Engine hinzukommt (die läuft über den SSE-Pfad, Phase 3).
"""

from __future__ import annotations

import asyncio
import time

from app import registry
from app.modelle.ergaenzung import ErgaenzungsAnfrage, ErgaenzungsAntwort, Vorschlag


def _verfuegbar(engine: object) -> bool:
    try:
        return bool(engine.ist_verfuegbar())  # type: ignore[attr-defined]
    except Exception:  # noqa: BLE001
        return False


def waehle_engines(angefragt: list[str] | None, *, nur_instant: bool) -> list[object]:
    alle = registry.ergaenzungs_engines.alle()
    if angefragt:
        gewuenscht = set(angefragt)
        kandidaten = [e for e in alle if e.engine_id in gewuenscht]
    else:
        kandidaten = [e for e in alle if e.standard_an]
    ausgewaehlt = [e for e in kandidaten if _verfuegbar(e)]
    if nur_instant:
        ausgewaehlt = [e for e in ausgewaehlt if not e.streaming]  # type: ignore[attr-defined]
    return ausgewaehlt


def mische(vorschlaege: list[Vorschlag], max_vorschlaege: int) -> list[Vorschlag]:
    """Nach Score sortieren und nach Einfügetext entdoppeln."""
    vorschlaege.sort(key=lambda v: v.score, reverse=True)
    gesehen: set[str] = set()
    ergebnis: list[Vorschlag] = []
    for v in vorschlaege:
        schluessel = v.text.strip().lower()
        if not schluessel or schluessel in gesehen:
            continue
        gesehen.add(schluessel)
        ergebnis.append(v)
        if len(ergebnis) >= max_vorschlaege:
            break
    return ergebnis


async def ergaenze(anfrage: ErgaenzungsAnfrage, *, kontext: str | None = None) -> ErgaenzungsAntwort:
    start = time.monotonic()
    engines = waehle_engines(anfrage.engines, nur_instant=True)

    ergebnisse = await asyncio.gather(
        *(e.ergaenze(anfrage, kontext) for e in engines),  # type: ignore[attr-defined]
        return_exceptions=True,
    )

    alle: list[Vorschlag] = []
    status: dict[str, str] = {}
    for engine, ergebnis in zip(engines, ergebnisse, strict=True):
        eid = engine.engine_id  # type: ignore[attr-defined]
        if isinstance(ergebnis, BaseException):
            status[eid] = "fehler"
            continue
        status[eid] = "ok"
        alle.extend(ergebnis)

    # Ob später ein LLM-Upgrade nachkommen könnte (Phase 3): wenn eine
    # streamende Engine aktiv/angefragt ist.
    streaming_moeglich = bool(waehle_engines(anfrage.engines, nur_instant=False)) and any(
        getattr(e, "streaming", False) for e in waehle_engines(anfrage.engines, nur_instant=False)
    )

    return ErgaenzungsAntwort(
        request_id=anfrage.request_id,
        erzeugt_ms=int((time.monotonic() - start) * 1000),
        vorschlaege=mische(alle, anfrage.max_vorschlaege),
        upgrade_aussteht=streaming_moeglich,
        engine_status=status,
    )
