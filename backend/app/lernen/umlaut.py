"""Hunspell-validierte Reparatur von ASCII-Umlaut-Ersatzschreibungen.

Wandelt ae/oe/ue/ss in echte Umlaute um - aber NUR, wenn dadurch ein deutsches
Wort entsteht, das Hunspell kennt, und die ASCII-Form selbst KEIN gueltiges Wort
ist. Dadurch bleiben echte Woerter wie 'neue', 'aktuell', 'dass', 'Adresse',
'Prozess' unangetastet, waehrend 'fuer'->'für', 'muessen'->'müssen',
'gruesse'->'grüße' korrigiert werden.

Wird beim Lernen (damit nie ASCII-Umlaute in Woerterbuch/N-Gramm wandern) und als
Sicherheitsnetz auf Modellausgaben angewandt. Ohne verfuegbares Woerterbuch ist
repariere() eine identische Abbildung (keine Aenderung).
"""

from __future__ import annotations

import re

from app.pruef_engines import hunspell_engine

_SITE = re.compile(r"ae|oe|ue|ss", re.IGNORECASE)
_UML = {"ae": "ä", "oe": "ö", "ue": "ü", "ss": "ß"}
_WORT = re.compile(r"[A-Za-zÄÖÜäöüß]+")
_MAX_STELLEN = 5


def _kandidaten(wort: str) -> list[str]:
    """Alle Formen, die durch Ersetzen einer Teilmenge der ae/oe/ue/ss-Stellen entstehen."""
    stellen = [(m.start(), m.group().lower()) for m in _SITE.finditer(wort)]
    if not stellen or len(stellen) > _MAX_STELLEN:
        return []
    ergebnisse: set[str] = set()
    anzahl = len(stellen)
    for maske in range(1, 1 << anzahl):  # mindestens eine Ersetzung
        s = wort
        versatz = 0
        for idx, (pos, bigr) in enumerate(stellen):
            if maske & (1 << idx):
                p = pos - versatz
                uml = _UML[bigr]
                if s[p].isupper():
                    uml = uml.upper()
                s = s[:p] + uml + s[p + 2 :]
                versatz += 1  # jede Ersetzung verkuerzt um ein Zeichen
        ergebnisse.add(s)
    # Formen mit mehr Umlauten zuerst (meist die korrekte Vollform).
    return sorted(ergebnisse, key=lambda w: sum(c in "äöüÄÖÜß" for c in w), reverse=True)


def repariere_wort(wort: str) -> str:
    """Gibt die umlautierte Form zurueck, wenn sie ein bekanntes Wort ist; sonst das Original."""
    if not _SITE.search(wort):
        return wort
    if hunspell_engine.kennt_wort(wort):  # ASCII-Form ist selbst gueltig (z. B. 'neue', 'dass')
        return wort
    for kandidat in _kandidaten(wort):
        if kandidat != wort and hunspell_engine.kennt_wort(kandidat):
            return kandidat
    return wort


def repariere(text: str) -> str:
    """Repariert alle Woerter eines Textes (nur echte ASCII-Umlaut-Faelle)."""
    if not _SITE.search(text):
        return text
    return _WORT.sub(lambda m: repariere_wort(m.group()), text)
