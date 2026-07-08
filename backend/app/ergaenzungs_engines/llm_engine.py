"""Kontextsensitive Textergaenzung ueber ein lokales Sprachmodell.

Streamt eine kurze Fortsetzung am Cursor (Fill-in-the-Middle: Text vor UND nach
dem Cursor gehen in den Prompt). Langsamer als Trie/N-Gramm, daher als
Upgrade ueber den SSE-Pfad (Phase 3). Der optionale `kontext` (Umfeld-Retrieval,
Phase 4) wird als Stilhinweis mitgegeben.
"""

from __future__ import annotations

import re
import uuid
from collections.abc import AsyncIterator
from typing import ClassVar

from app import config
from app.modelle.ergaenzung import ErgaenzungsAnfrage, ErgaenzungsModus, Vorschlag
from app.registry import ergaenzungs_engine
from app.services import llm_client

_SYSTEM = (
    "Du bist eine deutsche Schreibhilfe. Der Nutzer schreibt einen Text; die Marke <CURSOR> "
    "markiert die Schreibposition. Gib AUSSCHLIESSLICH den Text aus, der an <CURSOR> eingefuegt "
    "werden soll - wenige Woerter bis hoechstens ein Satz, passend zu Stil, Grammatik und "
    "Gross-/Kleinschreibung. Keine Wiederholung des vorhandenen Textes, keine Anfuehrungszeichen, "
    "keine Erklaerung. Wurde ein Wort begonnen, vervollstaendige genau dieses Wort ohne fuehrendes "
    "Leerzeichen."
)

_MAX_TOKENS = {
    ErgaenzungsModus.WORT: 8,
    ErgaenzungsModus.PHRASE: 24,
    ErgaenzungsModus.SATZ: 60,
}


def _nachrichten(anfrage: ErgaenzungsAnfrage, kontext: str | None) -> list[dict[str, str]]:
    system = _SYSTEM
    if kontext:
        system += f"\n\nStil-/Umfeld-Kontext des Nutzers (nur als Anhalt):\n{kontext}"
    inhalt = f"{anfrage.text_vor}<CURSOR>{anfrage.text_nach}"
    return [{"role": "system", "content": system}, {"role": "user", "content": inhalt}]


def _max_tokens(anfrage: ErgaenzungsAnfrage) -> int:
    return _MAX_TOKENS.get(anfrage.modus, 24)


_THINK_RE = re.compile(r"<think>.*?</think>", re.DOTALL | re.IGNORECASE)


def nachbereiten(anfrage: ErgaenzungsAnfrage, roh: str) -> Vorschlag | None:
    """Normalisiert die Modellausgabe zu einem einfuegbaren Vorschlag (Abstaende, Anfuehrung).

    Entfernt Reasoning-Bloecke (<think>...</think>). Enthaelt die Ausgabe nur ein
    offenes <think> ohne Abschluss (reines, abgeschnittenes Nachdenken), gibt es
    keinen brauchbaren Vorschlag - dann ist ein Nicht-Reasoning-Modell noetig.
    """
    ohne_think = _THINK_RE.sub("", roh)
    if "<think>" in ohne_think.lower():
        return None
    text = ohne_think.strip().strip('"').strip("'")
    # Nur die erste Zeile, ausser im Satz-/Phrasenmodus mit bewusstem Umbruch.
    if anfrage.modus == ErgaenzungsModus.WORT:
        text = text.split("\n", 1)[0]
    text = text.rstrip()
    if not text:
        return None

    # Endet der Text auf Buchstaben, gilt das als offenes Wort -> direkt weiterschreiben.
    # Endet er auf einem Trenner (Leerzeichen), ebenfalls kein zusaetzliches Leerzeichen.
    # In beiden Faellen wird ein fuehrendes Leerzeichen der Modellausgabe entfernt.
    if anfrage.text_vor and (anfrage.text_vor[-1].isalnum() or anfrage.text_vor[-1].isspace()):
        text = text.lstrip()

    if not text:
        return None
    return Vorschlag(
        id=uuid.uuid4().hex,
        text=text,
        engine="llm",
        score=0.9,
        art=anfrage.modus,
        final=True,
    )


@ergaenzungs_engine
class LlmEngine:
    engine_id: ClassVar[str] = "llm"
    name: ClassVar[str] = "Sprachmodell (kontextsensitiv)"
    standard_an: ClassVar[bool] = True
    streaming: ClassVar[bool] = True

    def ist_verfuegbar(self) -> bool:
        return llm_client.zuletzt_erreichbar()

    async def ergaenze(self, anfrage: ErgaenzungsAnfrage, kontext: str | None) -> list[Vorschlag]:
        """Einmalige (nicht streamende) Ergaenzung - fuer den Zwei-Ruf-Fallback."""
        try:
            roh = await llm_client.chat(
                _nachrichten(anfrage, kontext),
                temperature=0.2,
                max_tokens=_max_tokens(anfrage),
                timeout=config.LLM_KURZ_TIMEOUT_S,
            )
        except llm_client.LlmFehler:
            return []
        vorschlag = nachbereiten(anfrage, roh)
        return [vorschlag] if vorschlag else []

    async def stream(self, anfrage: ErgaenzungsAnfrage, kontext: str | None) -> AsyncIterator[str]:
        """Liefert die Text-Deltas der Ergaenzung (fuer den SSE-Pfad)."""
        async for delta in llm_client.chat_stream(
            _nachrichten(anfrage, kontext),
            temperature=0.2,
            max_tokens=_max_tokens(anfrage),
            timeout=config.LLM_TIMEOUT_S,
        ):
            yield delta
