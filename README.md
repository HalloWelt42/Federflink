# Federflink

Federflink ist ein lokal gehosteter Server für deutsche Rechtschreibung und
Textergänzung samt Browser-Erweiterung. Die Erweiterung zeigt in beliebigen
Eingabefeldern eine Copilot-artige Vorschau (grauer Geistertext), ohne den Text
automatisch einzufuegen: Tab übernimmt, Esc verwirft. Die gesamte Sprachlogik
liegt im Server, damit Clients dünn bleiben. Alles ist fein steuerbar und
abschaltbar. Betrieb zuerst auf dem Mac, später zentral auf einem Pi5.

## Aktueller Stand

- **Rechtschreibung**: Hunspell (deutsch, inkl. Komposita) mit Vorschlägen,
  optional LanguageTool (Grammatik); persönliches Wörterbuch filtert Bekanntes.
- **Korrektur**: neuronale Ganzsatz-Korrektur über ein lokales Sprachmodell,
  mit Schutznetzen gegen Halluzination und Prompt-Injection.
- **Ergänzung**: Wortvervollständigung (Trie), nächstes Wort/Phrase (N-Gramm,
  online lernend) und kontextsensitive LLM-Fortsetzung - per SSE als Progressive
  Enhancement (sofortiger Vorschlag, dann LLM-Upgrade).
- **Lernen**: Stufe 1 (persönliches Wörterbuch + N-Gramme) und Stufe 2
  (eigener Embedding-Kontextspeicher, self-contained) - beides über `/api/learn`.
- **Profile**: eingebaute + eigene Schreibprofile mit Stil und Host-Zuordnung.
- **Steuer-Oberfläche** (Svelte 5): Spielwiese für Rechtschreibung/Korrektur,
  Ergänzungs-Spielwiese mit Inline-Geistertext, Wörterbuch, Profile, Status;
  drei Themes.
- **Browser-Erweiterung** (`extension/`, MV3): Copilot-artige Vorschau in
  beliebigen Feldern; Tab übernimmt, Esc verwirft; fein steuerbar, abschaltbar.
- **Dokumentation** (`docs/`): mehrteilig, inkl. vollständiger API und
  Integrationsleitfaden für eigene Programme.

Details und Integration: siehe [docs/](docs/).

## Starten

```bash
./start.sh start     # Backend + Frontend starten (richtet beim ersten Mal alles ein)
./start.sh stop      # stoppen
./start.sh status    # Laufstatus
./start.sh logs      # Logs live
```

Frontend: http://localhost:5195   Backend: 127.0.0.1:8500 (oder nächster freier Port)

## Projektstruktur

```
Federflink/
  start.sh          Start/Stop von Backend + Frontend
  version.json      einzige Quelle der Versionsnummer
  backend/          FastAPI + Pydantic + SQLite (die gesamte Sprachlogik)
  frontend/         Svelte 5 + TypeScript (Steuer-Oberfläche)
  extension/        Browser-Erweiterung (MV3, reines JS)
  docs/             mehrteilige Dokumentation und Integrationsanleitung
  data/             Datenbank und Wörterbücher (bleiben lokal)
```

## Stack

| Baustein   | Technik                                             | Port |
|------------|-----------------------------------------------------|------|
| Backend    | Python 3.12+, FastAPI, Pydantic v2, SQLite          | 8500 |
| Frontend   | Svelte 5, TypeScript, Vite                          | 5195 |
| Erweiterung| WebExtension (Manifest V3, reines JavaScript)       | -    |
| Sprachmodell | Lokaler OpenAI-kompatibler Server (LM Studio / Ollama / llama.cpp) | 1234 / 11434 |

## Unterstützen

Federflink ist ein privates Open-Source-Projekt. Kein Tracking, keine Werbung, keine Kompromisse.

Wenn dir das Projekt gefällt, kannst du hier "Danke sagen":

[![Ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/HalloWelt42)

**Crypto:**

| Coin | Adresse |
|------|---------|
| BTC | `bc1qnd599khdkv3v3npmj9ufxzf6h4fzanny2acwqr` |
| DOGE | `DL7tuiYCqm3xQjMDXChdxeQxqUGMACn1ZV` |
| ETH | `0x8A28fc47bFFFA03C8f685fa0836E2dBe1CA14F27` |

## Lizenz

Nicht-kommerzielle Lizenz v1.0 - siehe [LICENSE](LICENSE).
