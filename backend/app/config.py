"""Zentrale Konfiguration: Pfade, Ports, LLM-Anbindung, Ergaenzungs-Grenzen.

Alle Werte sind per Umgebungsvariable uebersteuerbar (Praefix FEDERFLINK_).
Die hier definierten Werte sind die eingebauten Standardwerte; die im UI
aenderbaren Betriebseinstellungen liegen zusaetzlich in der Settings-Tabelle
der Datenbank (siehe app.services.einstellungen) und haben Vorrang.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

PROJEKT_WURZEL = Path(__file__).resolve().parents[2]
VERSIONSDATEI = PROJEKT_WURZEL / "version.json"


def _lies_version() -> str:
    try:
        daten = json.loads(VERSIONSDATEI.read_text(encoding="utf-8"))
        version = daten.get("version")
        return version if isinstance(version, str) else "0.0.0"
    except (OSError, ValueError):
        return "0.0.0"


def _env_int(name: str, standard: int) -> int:
    wert = os.environ.get(name)
    if wert is None:
        return standard
    try:
        return int(wert)
    except ValueError:
        return standard


def _env_str(name: str, standard: str) -> str:
    wert = os.environ.get(name)
    return wert if wert is not None else standard


def _env_bool(name: str, standard: bool) -> bool:
    wert = os.environ.get(name)
    if wert is None:
        return standard
    return wert.strip().lower() in ("1", "true", "ja", "yes", "on")


APP_VERSION: str = _lies_version()

# ----------------------------------------------------------------------------
# Ablage: Datenbank und Woerterbuecher liegen im Projekt (nichts verlaesst den Ordner)
# ----------------------------------------------------------------------------
DATEN_VERZEICHNIS: Path = Path(_env_str("FEDERFLINK_DATEN_DIR", str(PROJEKT_WURZEL / "data")))
DB_PFAD: Path = Path(_env_str("FEDERFLINK_DB_PFAD", str(DATEN_VERZEICHNIS / "federflink.db")))
WOERTERBUCH_VERZEICHNIS: Path = Path(
    _env_str("FEDERFLINK_WOERTERBUCH_DIR", str(DATEN_VERZEICHNIS / "woerterbuecher"))
)

# ----------------------------------------------------------------------------
# CORS: Vite-Entwicklungsserver und die Browser-Erweiterung
# ----------------------------------------------------------------------------
FRONTEND_PORT: int = _env_int("FEDERFLINK_FRONTEND_PORT", 5195)
FRONTEND_URSPRUENGE: tuple[str, ...] = (
    f"http://localhost:{FRONTEND_PORT}",
    f"http://127.0.0.1:{FRONTEND_PORT}",
)
# Die Erweiterung (Service-Worker) ruft die API von ihrem chrome-extension-Ursprung
# aus auf. Da der Server ohnehin nur an localhost lauscht, ist das unbedenklich.
EXTENSION_URSPRUNG_REGEX: str = _env_str(
    "FEDERFLINK_EXTENSION_ORIGIN_REGEX", r"^(chrome-extension|moz-extension)://.*$"
)

# ----------------------------------------------------------------------------
# LLM-Anbindung an einen lokalen, OpenAI-kompatiblen Server
# (LM Studio auf dem Mac :1234, Ollama auf dem Pi :11434, llama.cpp - alle kompatibel)
# ----------------------------------------------------------------------------
LLM_URL: str = _env_str("FEDERFLINK_LLM_URL", "http://localhost:1234")
DEFAULT_CHAT_MODELL: str = _env_str("FEDERFLINK_CHAT_MODELL", "")
DEFAULT_EMBEDDING_MODELL: str = _env_str("FEDERFLINK_EMBEDDING_MODELL", "")
LLM_TIMEOUT_S: float = float(_env_int("FEDERFLINK_LLM_TIMEOUT_S", 30))
LLM_KURZ_TIMEOUT_S: float = float(_env_int("FEDERFLINK_LLM_KURZ_TIMEOUT_S", 12))

# ----------------------------------------------------------------------------
# Ergaenzungs-Grenzen (Standardwerte; im UI/Settings feiner steuerbar)
# ----------------------------------------------------------------------------
# Kontextfenster, das der Client um den Cursor herum senden darf.
BUDGET_VOR_ZEICHEN: int = _env_int("FEDERFLINK_BUDGET_VOR", 800)
BUDGET_NACH_ZEICHEN: int = _env_int("FEDERFLINK_BUDGET_NACH", 200)
# Client-Entprellung und Mindestlaenge, bevor ueberhaupt angefragt wird.
DEBOUNCE_MS: int = _env_int("FEDERFLINK_DEBOUNCE_MS", 150)
MIN_ZEICHEN: int = _env_int("FEDERFLINK_MIN_ZEICHEN", 3)
MAX_VORSCHLAEGE: int = _env_int("FEDERFLINK_MAX_VORSCHLAEGE", 3)
# Maximale Textlaenge einer Rechtschreib-/Korrektur-Anfrage (Schutz vor Missbrauch).
MAX_TEXT_ZEICHEN: int = _env_int("FEDERFLINK_MAX_TEXT_ZEICHEN", 20000)
