# Federflink - Architektur

Der Überblick der Schichten steht in [00_UEBERBLICK.md](00_UEBERBLICK.md).

## Backend-Aufbau

- `app/main.py` - App-Fabrik (Middleware, Fehler-Handler, DB-Init, Router).
- `app/registry.py` - typisierte Registries + Dekoratoren + `entdecke_module()`;
  baut die `capabilities()`-Antwort.
- `app/schnittstellen/` - die Protokolle `PruefEngine` und `ErgaenzungsEngine`.
- `app/pruef_engines/` - eine Datei je Rechtschreib-/Grammatik-Verfahren.
- `app/ergaenzungs_engines/` - eine Datei je Ergänzungs-Verfahren.
- `app/dispatcher.py` - führt Ergänzungs-Engines aus, mischt und rankt.
- `app/lernen/` - Wörterbuch, N-Gramm, Umfeld-Kontext, Telemetrie.
- `app/profile/` - Schreibprofile.
- `app/services/` - LLM-Client, Korrektur, zentrale Einstellungen.
- `app/persistence/` - SQLite (Schema + Verbindungen).

## Datenfluss der Ergänzung

1. Client sendet Kontext um den Cursor an `POST /api/complete`.
2. Dispatcher fragt schnelle Engines (Trie/N-Gramm) - Instant-Vorschlag.
3. Dispatcher fragt die LLM-Engine (mit Umfeld-Kontext) - Upgrade per SSE.
4. Client ersetzt den Geistertext nur, wenn `request_id` + `kontext_hash` passen.

## Graceful Degradation

Jede Engine kapselt ihre Fehler. Fällt die LLM-Engine oder LanguageTool aus,
bleiben Hunspell bzw. Trie/N-Gramm aktiv. Der Client erfährt den Zustand über
`capabilities` und `engine_status`.
