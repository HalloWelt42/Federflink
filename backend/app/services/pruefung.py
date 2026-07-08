"""Orchestriert die Rechtschreib-/Grammatikpruefung ueber mehrere Engines.

Waehlt die Engines (angefragte oder die standardmaessig aktiven), fuehrt sie aus,
filtert bekannte Woerter aus dem persoenlichen Woerterbuch heraus und liefert die
zusammengefuehrten Befunde.
"""

from __future__ import annotations

import time

from app import config, registry
from app.fehler import LimitUeberschritten
from app.lernen import woerterbuch
from app.modelle.pruefung import Befund, BefundArt, PruefAnfrage, PruefAntwort


def _ausgewaehlte_engines(angefragt: list[str] | None) -> list[object]:
    alle = registry.pruef_engines.alle()
    if angefragt:
        gewuenscht = set(angefragt)
        return [e for e in alle if e.engine_id in gewuenscht and _verfuegbar(e)]
    # Vorgabe: alle standardmaessig aktiven und verfuegbaren Engines.
    return [e for e in alle if e.standard_an and _verfuegbar(e)]


def _verfuegbar(engine: object) -> bool:
    try:
        return bool(engine.ist_verfuegbar())  # type: ignore[attr-defined]
    except Exception:  # noqa: BLE001
        return False


def fuehre_pruefung(anfrage: PruefAnfrage) -> PruefAntwort:
    if len(anfrage.text) > config.MAX_TEXT_ZEICHEN:
        raise LimitUeberschritten(
            f"Text zu lang ({len(anfrage.text)} Zeichen, erlaubt {config.MAX_TEXT_ZEICHEN})."
        )

    start = time.monotonic()
    engines = _ausgewaehlte_engines(anfrage.engines)
    bekannt = woerterbuch.bekannte_woerter(anfrage.profil_id)

    befunde: list[Befund] = []
    gelaufen: list[str] = []
    for engine in engines:
        try:
            teil = engine.pruefe(anfrage.text, anfrage.sprache)  # type: ignore[attr-defined]
        except Exception:  # noqa: BLE001 - eine Engine darf die anderen nicht stoppen
            continue
        gelaufen.append(engine.engine_id)  # type: ignore[attr-defined]
        befunde.extend(teil)

    gefiltert = [b for b in befunde if not _im_woerterbuch(b, anfrage.text, bekannt)]
    gefiltert.sort(key=lambda b: (b.offset, b.laenge))

    dauer = int((time.monotonic() - start) * 1000)
    return PruefAntwort(befunde=gefiltert, engines=gelaufen, dauer_ms=dauer)


def _im_woerterbuch(befund: Befund, text: str, bekannt: set[str]) -> bool:
    """Rechtschreib-Befunde fuer im persoenlichen Woerterbuch bekannte Woerter verwerfen."""
    if befund.art != BefundArt.RECHTSCHREIBUNG:
        return False
    wort = text[befund.offset : befund.offset + befund.laenge].lower()
    return wort in bekannt
