"""Kontextsensitive Textergänzung über ein lokales Sprachmodell.

Streamt eine kurze Fortsetzung am Cursor (Fill-in-the-Middle: Text vor UND nach
dem Cursor gehen in den Prompt). Langsamer als Trie/N-Gramm, daher als
Upgrade über den SSE-Pfad (Phase 3). Der optionale `kontext` (Umfeld-Retrieval,
Phase 4) wird als Stilhinweis mitgegeben.
"""

from __future__ import annotations

import re
import uuid
from collections.abc import AsyncIterator
from typing import ClassVar

from app import config
from app.lernen import tokens, umlaut
from app.modelle.ergaenzung import ErgaenzungsAnfrage, ErgaenzungsModus, Vorschlag
from app.registry import ergaenzungs_engine
from app.services import llm_client

_SYSTEM = (
    "Du bist eine deutsche Schreibhilfe. Der Nutzer schreibt einen Text; die Marke <CURSOR> "
    "markiert die Schreibposition. Gib AUSSCHLIESSLICH den Text aus, der an <CURSOR> eingefügt "
    "werden soll - wenige Wörter bis höchstens ein Satz, passend zu Stil, Grammatik und "
    "Groß-/Kleinschreibung. Keine Wiederholung des vorhandenen Textes, keine Anführungszeichen, "
    "keine Erklärung. Wurde ein Wort begonnen, vervollständige genau dieses Wort ohne führendes "
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
    """Normalisiert die Modellausgabe zu einem einfügbaren Vorschlag (Abstände, Anführung).

    Entfernt Reasoning-Blöcke (<think>...</think>). Enthält die Ausgabe nur ein
    offenes <think> ohne Abschluss (reines, abgeschnittenes Nachdenken), gibt es
    keinen brauchbaren Vorschlag - dann ist ein Nicht-Reasoning-Modell nötig.
    """
    ohne_think = _THINK_RE.sub("", roh)
    if "<think>" in ohne_think.lower():
        return None
    text = ohne_think.strip().strip('"').strip("'")
    # Nur die erste Zeile, außer im Satz-/Phrasenmodus mit bewusstem Umbruch.
    if anfrage.modus == ErgaenzungsModus.WORT:
        text = text.split("\n", 1)[0]
    text = text.rstrip()
    if not text:
        return None

    # Endet der Text auf Buchstaben, gilt das als offenes Wort -> direkt weiterschreiben.
    # Endet er auf einem Trenner (Leerzeichen), ebenfalls kein zusätzliches Leerzeichen.
    # In beiden Fällen wird ein führendes Leerzeichen der Modellausgabe entfernt.
    if anfrage.text_vor and (anfrage.text_vor[-1].isalnum() or anfrage.text_vor[-1].isspace()):
        text = text.lstrip()

    if not text:
        return None
    text = umlaut.repariere(text)  # Sicherheitsnetz gegen ASCII-Umlaute des Modells
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
        """Einmalige (nicht streamende) Ergänzung - für den Zwei-Ruf-Fallback."""
        if tokens.letztes_teilwort(anfrage.text_vor):
            return []  # mitten im Wort: der Trie (echte Wortlisten) ist zustaendig
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
        """Liefert die Text-Deltas der Ergänzung (für den SSE-Pfad)."""
        if tokens.letztes_teilwort(anfrage.text_vor):
            return  # mitten im Wort: kein LLM (der Trie vervollstaendigt das Wort)
        async for delta in llm_client.chat_stream(
            _nachrichten(anfrage, kontext),
            temperature=0.2,
            max_tokens=_max_tokens(anfrage),
            timeout=config.LLM_TIMEOUT_S,
        ):
            yield delta
