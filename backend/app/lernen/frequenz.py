"""Häufigkeits-Index für die Wortvervollständigung (Trie-Ersatz per bisect).

Lädt die deutsche Häufigkeitsliste (data/woerterbuecher/de_frequenz.txt) einmalig
in eine sortierte Liste + Häufigkeits-Tabelle. Präfix-Suchen laufen über bisect
und werden nach Häufigkeit sortiert. Alles klein geschrieben - die korrekte
Groß-/Kleinschreibung ergibt sich beim Vorschlag aus dem bereits getippten Präfix.
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
    _entferne_ascii_dubletten(freq)
    woerter = sorted(freq)
    return woerter, freq


def _entferne_ascii_dubletten(freq: dict[str, int]) -> None:
    """Entfernt ASCII-Umlaut-Varianten, wenn die echte Umlaut-Form vorhanden ist
    (z. B. 'fuer' neben 'für'). So schlaegt der Trie nie ae/oe/ue vor. 'ss'->'ß'
    wird bewusst ausgelassen (zu heikel: 'dass'/'Adresse')."""
    for wort in list(freq):
        if "ae" in wort or "oe" in wort or "ue" in wort:
            kandidat = wort.replace("ae", "ä").replace("oe", "ö").replace("ue", "ü")
            if kandidat != wort and kandidat in freq:
                del freq[wort]


def verfuegbar() -> bool:
    return (config.WOERTERBUCH_VERZEICHNIS / "de_frequenz.txt").exists()


def vervollstaendige(praefix_klein: str, top: int = 5) -> list[tuple[str, int]]:
    """Liefert (Wort, Häufigkeit) für Wörter, die mit dem Präfix beginnen."""
    woerter, freq = _index()
    if not woerter or not praefix_klein:
        return []
    links = bisect.bisect_left(woerter, praefix_klein)
    rechts = bisect.bisect_left(woerter, praefix_klein + "￿")
    treffer = woerter[links:rechts]
    # Das identische Wort (Präfix == Wort) ist keine Vervollständigung.
    treffer = [w for w in treffer if w != praefix_klein]
    treffer.sort(key=lambda w: freq.get(w, 0), reverse=True)
    return [(w, freq.get(w, 0)) for w in treffer[:top]]
