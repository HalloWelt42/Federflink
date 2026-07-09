"""Satz-Vorschläge: verbessert EINEN Satz, der zwar korrekt geschriebene Wörter
enthält, im Kontext aber unlogisch oder falsch in Wortwahl/Grammatik ist.

Bewusst auf genau einen Satz begrenzt - das hält die Anfrage klein und schnell,
sodass die (bis zu drei) Vorschläge zügig zur Auswahl stehen. Ein LLM-Aufruf
liefert die Varianten als JSON-Array; die Ausgabe wird robust geparst und
gegen Reasoning-Ausgaben (<think>) abgesichert.
"""

from __future__ import annotations

import json
import re

from app import config
from app.lernen import umlaut
from app.profile import dienst as profil_dienst
from app.services import llm_client

_MAX_VORSCHLAEGE = 3
_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)
_LISTEN_PRAEFIX = re.compile(r"^\s*(?:[-*•]|\d+[.)])\s*")

_SYSTEM = (
    "Du bist eine deutsche Schreibhilfe. Der Nutzer gibt GENAU EINEN Satz. Der Satz kann "
    "inhaltlich unlogisch sein oder eine falsche Wortwahl bzw. Grammatik enthalten, obwohl alle "
    "Wörter richtig geschrieben sind. Gib bis zu drei verbesserte, natürliche und sinnvolle "
    "Varianten GENAU DIESES EINEN Satzes zurück - als reines JSON-Array von Strings, sonst nichts. "
    "Betrachte nur diesen Satz, erfinde keine neuen Fakten, behalte die Bedeutung so weit wie "
    "möglich bei. Ist der Satz bereits gut und logisch, gib ein leeres Array [] zurück. "
    "Verwende korrekte deutsche Umlaute (ä, ö, ü, ß)."
)


def _parse(roh: str) -> list[str]:
    """Liest die Varianten aus der Modellausgabe (JSON-Array bevorzugt, sonst Zeilen)."""
    text = _THINK_RE.sub("", roh).strip()
    anfang = text.find("[")
    ende = text.rfind("]")
    if anfang != -1 and ende > anfang:
        try:
            daten = json.loads(text[anfang : ende + 1])
            if isinstance(daten, list):
                return [str(x).strip() for x in daten if str(x).strip()]
        except json.JSONDecodeError:
            pass
    # Rückfall: Zeilen, evtl. mit Aufzählungszeichen/Nummerierung.
    zeilen = [_LISTEN_PRAEFIX.sub("", z).strip().strip('"') for z in text.splitlines()]
    return [z for z in zeilen if z]


async def vorschlaege(satz: str, *, profil_id: str | None = None, modell: str | None = None) -> list[str]:
    """Bis zu drei verbesserte Varianten des Satzes; leer, wenn nichts nötig/erreichbar."""
    satz = (satz or "").strip()
    if len(satz) < 3:
        return []

    stil = profil_dienst.stil_prompt(profil_id or "standard")
    system = _SYSTEM + (f"\nStil-Hinweis: {stil}" if stil else "")

    try:
        roh = await llm_client.chat(
            [{"role": "system", "content": system}, {"role": "user", "content": satz}],
            model=modell,
            temperature=0.4,
            max_tokens=min(240, max(48, len(satz) * 4)),
            timeout=config.LLM_KURZ_TIMEOUT_S,
        )
    except llm_client.LlmFehler:
        return []

    ergebnis: list[str] = []
    for kandidat in _parse(roh):
        kandidat = umlaut.repariere(_THINK_RE.sub("", kandidat).strip().strip('"'))
        if not kandidat or kandidat == satz or kandidat in ergebnis:
            continue
        ergebnis.append(kandidat)
        if len(ergebnis) >= _MAX_VORSCHLAEGE:
            break
    return ergebnis
