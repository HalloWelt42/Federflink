"""Grammatik-, Zeichensetzungs- und Stilpruefung mit LanguageTool (optional).

Regelbasiert - folgt keinen Anweisungen im Text und halluziniert nicht. Benoetigt
Java und das Paket language-tool-python (Extra 'grammatik'). Ist eines davon nicht
vorhanden, meldet sich die Engine inaktiv; Federflink laeuft dann mit Hunspell + LLM.

Standardmaessig ausgeschaltet (Java-Prozess ~1 GB) - im UI zuschaltbar.
"""

from __future__ import annotations

import shutil
from typing import ClassVar

from app.modelle.pruefung import Befund, BefundArt
from app.registry import pruef_engine

_KATEGORIE_ZU_ART = {
    "TYPOS": BefundArt.RECHTSCHREIBUNG,
    "SPELLING": BefundArt.RECHTSCHREIBUNG,
    "GRAMMAR": BefundArt.GRAMMATIK,
    "PUNCTUATION": BefundArt.ZEICHENSETZUNG,
    "TYPOGRAPHY": BefundArt.ZEICHENSETZUNG,
}

_MAX_VORSCHLAEGE = 5
_MAX_BEFUNDE = 300

_tool = None
_init_versucht = False


def _lade_tool() -> object | None:
    global _tool, _init_versucht
    if _init_versucht:
        return _tool
    _init_versucht = True
    try:
        import language_tool_python

        _tool = language_tool_python.LanguageTool("de-DE")
    except Exception:  # noqa: BLE001 - kein Java / kein Paket / Download fehlgeschlagen
        _tool = None
    return _tool


@pruef_engine
class LanguageToolEngine:
    engine_id: ClassVar[str] = "languagetool"
    name: ClassVar[str] = "LanguageTool (Grammatik)"
    standard_an: ClassVar[bool] = False

    def ist_verfuegbar(self) -> bool:
        """Leichtgewichtige Pruefung ohne die teure Tool-Initialisierung."""
        if shutil.which("java") is None:
            return False
        try:
            import language_tool_python  # noqa: F401
        except Exception:  # noqa: BLE001
            return False
        return True

    def pruefe(self, text: str, sprache: str) -> list[Befund]:
        if not sprache.lower().startswith("de"):
            return []
        tool = _lade_tool()
        if tool is None:
            return []
        try:
            treffer = tool.check(text)  # type: ignore[attr-defined]
        except Exception:  # noqa: BLE001
            return []

        befunde: list[Befund] = []
        for m in treffer[:_MAX_BEFUNDE]:
            kategorie = str(getattr(m, "category", "") or "").upper()
            regel = str(getattr(m, "ruleId", "") or "")
            art = _KATEGORIE_ZU_ART.get(kategorie, BefundArt.STIL)
            if "SPELL" in regel or "MORFOLOGIK" in regel:
                art = BefundArt.RECHTSCHREIBUNG
            befunde.append(
                Befund(
                    offset=int(getattr(m, "offset", 0)),
                    laenge=int(getattr(m, "errorLength", 0)),
                    art=art,
                    meldung=str(getattr(m, "message", "") or ""),
                    regel_id=regel or None,
                    vorschlaege=list(getattr(m, "replacements", []) or [])[:_MAX_VORSCHLAEGE],
                    engine=self.engine_id,
                )
            )
        return befunde
