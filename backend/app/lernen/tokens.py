"""Kleine Wort-Werkzeuge, geteilt von Engines und Lernspeichern."""

from __future__ import annotations

import re

_WORT = re.compile(r"[A-Za-zÄÖÜäöüß]+(?:['-][A-Za-zÄÖÜäöüß]+)*")
_TEILWORT_AM_ENDE = re.compile(r"[A-Za-zÄÖÜäöüß]+$")


def woerter(text: str) -> list[str]:
    """Alle Wörter in Originalschreibung."""
    return _WORT.findall(text)


def letztes_teilwort(text_vor: str) -> str:
    """Das gerade getippte, noch offene Wort am Cursor (leer, wenn danach ein Trenner steht)."""
    treffer = _TEILWORT_AM_ENDE.search(text_vor)
    return treffer.group() if treffer else ""
