"""Rechtschreibpruefung auf Wortebene mit Hunspell (reines Python via spylls).

Nutzt das deutsche Woerterbuch unter data/woerterbuecher/de_DE.{aff,dic}
(einmalig via tools/hole_woerterbuch.py laden). Erkennt deutsche Komposita und
liefert Korrekturvorschlaege. Sehr schnell und ressourcenschonend - laeuft auf
Mac und Pi identisch, kein Java noetig.
"""

from __future__ import annotations

import re
from typing import ClassVar

from app import config
from app.modelle.pruefung import Befund, BefundArt
from app.registry import pruef_engine

# Wortsequenzen aus Buchstaben (inkl. Umlaute/ß), optional mit Binde-/Apostroph im Inneren.
_WORT_RE = re.compile(r"[A-Za-zÄÖÜäöüß]+(?:['-][A-Za-zÄÖÜäöüß]+)*")

_MAX_VORSCHLAEGE = 5
_MAX_BEFUNDE = 300

# Modul-weite, faul geladene Woerterbuch-Instanz (Laden dauert einmalig ~1-2 s).
_dict = None
_geladen = False


def _lade_dict() -> object | None:
    global _dict, _geladen
    if _geladen:
        return _dict
    _geladen = True
    basis = config.WOERTERBUCH_VERZEICHNIS / "de_DE"
    if not (basis.with_suffix(".aff").exists() and basis.with_suffix(".dic").exists()):
        _dict = None
        return None
    try:
        from spylls.hunspell import Dictionary

        _dict = Dictionary.from_files(str(basis))
    except Exception:  # noqa: BLE001 - fehlendes/kaputtes Woerterbuch darf nicht crashen
        _dict = None
    return _dict


def kennt_wort(wort: str) -> bool | None:
    """True/False, ob das Woerterbuch das Wort kennt; None, wenn kein Woerterbuch da ist.

    Wird beim Lernen genutzt, um nur wirklich unbekannte Woerter ins persoenliche
    Woerterbuch aufzunehmen (statt es mit Allerweltswoertern zu fluten).
    """
    woerterbuch = _lade_dict()
    if woerterbuch is None:
        return None
    try:
        return bool(woerterbuch.lookup(wort))  # type: ignore[attr-defined]
    except Exception:  # noqa: BLE001
        return None


@pruef_engine
class HunspellEngine:
    engine_id: ClassVar[str] = "hunspell"
    name: ClassVar[str] = "Hunspell (Rechtschreibung)"
    standard_an: ClassVar[bool] = True

    def ist_verfuegbar(self) -> bool:
        basis = config.WOERTERBUCH_VERZEICHNIS / "de_DE"
        return basis.with_suffix(".aff").exists() and basis.with_suffix(".dic").exists()

    def pruefe(self, text: str, sprache: str) -> list[Befund]:
        if not sprache.lower().startswith("de"):
            return []
        woerterbuch = _lade_dict()
        if woerterbuch is None:
            return []

        befunde: list[Befund] = []
        for treffer in _WORT_RE.finditer(text):
            if len(befunde) >= _MAX_BEFUNDE:
                break
            wort = treffer.group()
            if len(wort) < 2:
                continue
            try:
                if woerterbuch.lookup(wort):
                    continue
                vorschlaege = _hole_vorschlaege(woerterbuch, wort)
            except Exception:  # noqa: BLE001 - einzelnes Wort darf die Pruefung nicht stoppen
                continue
            befunde.append(
                Befund(
                    offset=treffer.start(),
                    laenge=len(wort),
                    art=BefundArt.RECHTSCHREIBUNG,
                    meldung=f"Moegliche falsche Schreibweise: {wort}",
                    vorschlaege=vorschlaege,
                    engine=self.engine_id,
                )
            )
        return befunde


def _hole_vorschlaege(woerterbuch: object, wort: str) -> list[str]:
    vorschlaege: list[str] = []
    for vorschlag in woerterbuch.suggest(wort):  # type: ignore[attr-defined]
        vorschlaege.append(vorschlag)
        if len(vorschlaege) >= _MAX_VORSCHLAEGE:
            break
    return vorschlaege
