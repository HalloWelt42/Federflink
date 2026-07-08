"""Haeufigkeits-Index fuer die Wortvervollstaendigung (Trie-Ersatz per bisect).

Laedt die deutsche Haeufigkeitsliste (data/woerterbuecher/de_frequenz.txt) einmalig
in eine sortierte Liste + Haeufigkeits-Tabelle. Praefix-Suchen laufen ueber bisect
und werden nach Haeufigkeit sortiert. Alles klein geschrieben - die korrekte
Gross-/Kleinschreibung ergibt sich beim Vorschlag aus dem bereits getippten Praefix.
"""

from __future__ import annotations

import bisect
import functools

from app import config


@functools.lru_cache(maxsize=1)
def _index() -> tuple[list[str], dict[str, int]]:
    pfad = config.WOERTERBUCH_VERZEICHNIS / "de_frequenz.txt"
    freq: dict[str, int] = {}
    if pfad.exists():
        for zeile in pfad.read_text(encoding="utf-8", errors="ignore").splitlines():
            teile = zeile.split()
            if len(teile) != 2:
                continue
            wort, zahl = teile
            if not zahl.isdigit() or len(wort) < 2:
                continue
            freq[wort.lower()] = int(zahl)
    woerter = sorted(freq)
    return woerter, freq


def verfuegbar() -> bool:
    return (config.WOERTERBUCH_VERZEICHNIS / "de_frequenz.txt").exists()


def vervollstaendige(praefix_klein: str, top: int = 5) -> list[tuple[str, int]]:
    """Liefert (Wort, Haeufigkeit) fuer Woerter, die mit dem Praefix beginnen."""
    woerter, freq = _index()
    if not woerter or not praefix_klein:
        return []
    links = bisect.bisect_left(woerter, praefix_klein)
    rechts = bisect.bisect_left(woerter, praefix_klein + "￿")
    treffer = woerter[links:rechts]
    # Das identische Wort (Praefix == Wort) ist keine Vervollstaendigung.
    treffer = [w for w in treffer if w != praefix_klein]
    treffer.sort(key=lambda w: freq.get(w, 0), reverse=True)
    return [(w, freq.get(w, 0)) for w in treffer[:top]]
