# Federflink - Betrieb auf dem Pi5

> Wird mit Phase 6 ausgebaut.

## Kurzfassung

- Backend + Frontend laufen bare via `./start.sh` (kein Docker noetig).
- Das Sprachmodell laeuft auf dem Pi ueber Ollama (ARM64, OpenAI-kompatibel,
  Standard-Port 11434) oder llama.cpp. In `backend/app/config.py` bzw. den
  Einstellungen die `LLM_URL` auf `http://localhost:11434` setzen.
- Hunspell (spylls) braucht kein Java und laeuft direkt. LanguageTool ist optional
  (Java, ~1 GB) und kann auf dem Pi abgeschaltet bleiben.
- Datenbank und Woerterbuecher liegen unter `data/` auf dem lokalen Dateisystem
  (ext4). Kein Netzlaufwerk/Bind-Mount fuer die SQLite-Datei verwenden.

## Empfohlene Modelle

Siehe [09_MODELLE.md](09_MODELLE.md).
