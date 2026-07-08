# Federflink

Federflink ist ein lokal gehosteter Server fuer deutsche Rechtschreibung und
Textergaenzung samt Browser-Erweiterung. Die Erweiterung zeigt in beliebigen
Eingabefeldern eine Copilot-artige Vorschau (grauer Geistertext), ohne den Text
automatisch einzufuegen: Tab uebernimmt, Esc verwirft. Die gesamte Sprachlogik
liegt im Server, damit Clients duenn bleiben. Alles ist fein steuerbar und
abschaltbar. Betrieb zuerst auf dem Mac, spaeter zentral auf einem Pi5.

## Aktueller Stand

- **Rechtschreibung**: Hunspell (deutsch, inkl. Komposita) mit Vorschlaegen,
  optional LanguageTool (Grammatik); persoenliches Woerterbuch filtert Bekanntes.
- **Korrektur**: neuronale Ganzsatz-Korrektur ueber ein lokales Sprachmodell,
  mit Schutznetzen gegen Halluzination und Prompt-Injection.
- **Ergaenzung**: Wortvervollstaendigung (Trie), naechstes Wort/Phrase (N-Gramm,
  online lernend) und kontextsensitive LLM-Fortsetzung - per SSE als Progressive
  Enhancement (sofortiger Vorschlag, dann LLM-Upgrade).
- **Lernen**: Stufe 1 (persoenliches Woerterbuch + N-Gramme) und Stufe 2
  (eigener Embedding-Kontextspeicher, self-contained) - beides ueber `/api/learn`.
- **Profile**: eingebaute + eigene Schreibprofile mit Stil und Host-Zuordnung.
- **Steuer-Oberflaeche** (Svelte 5): Spielwiese fuer Rechtschreibung/Korrektur,
  Ergaenzungs-Spielwiese mit Inline-Geistertext, Woerterbuch, Profile, Status;
  drei Themes.
- **Browser-Erweiterung** (`extension/`, MV3): Copilot-artige Vorschau in
  beliebigen Feldern; Tab uebernimmt, Esc verwirft; fein steuerbar, abschaltbar.
- **Dokumentation** (`docs/`): mehrteilig, inkl. vollstaendiger API und
  Integrationsleitfaden fuer eigene Programme.

Details und Integration: siehe [docs/](docs/).

## Starten

```bash
./start.sh start     # Backend + Frontend starten (richtet beim ersten Mal alles ein)
./start.sh stop      # stoppen
./start.sh status    # Laufstatus
./start.sh logs      # Logs live
```

Frontend: http://localhost:5195   Backend: 127.0.0.1:8500 (oder naechster freier Port)

## Projektstruktur

```
Federflink/
  start.sh          Start/Stop von Backend + Frontend
  version.json      einzige Quelle der Versionsnummer
  backend/          FastAPI + Pydantic + SQLite (die gesamte Sprachlogik)
  frontend/         Svelte 5 + TypeScript (Steuer-Oberflaeche)
  extension/        Browser-Erweiterung (MV3, reines JS)
  docs/             mehrteilige Dokumentation und Integrationsanleitung
  data/             Datenbank und Woerterbuecher (bleiben lokal)
```

## Stack

| Baustein   | Technik                                             | Port |
|------------|-----------------------------------------------------|------|
| Backend    | Python 3.12+, FastAPI, Pydantic v2, SQLite          | 8500 |
| Frontend   | Svelte 5, TypeScript, Vite                          | 5195 |
| Erweiterung| WebExtension (Manifest V3, reines JavaScript)       | -    |
| Sprachmodell | Lokaler OpenAI-kompatibler Server (LM Studio / Ollama / llama.cpp) | 1234 / 11434 |

## Unterstuetzen

Federflink ist ein privates Open-Source-Projekt. Kein Tracking, keine Werbung, keine Kompromisse.

Wenn dir das Projekt gefaellt, kannst du hier "Danke sagen":

[![Ko-fi](https://ko-fi.com/img/githubbutton_sm.svg)](https://ko-fi.com/HalloWelt42)

**Crypto:**

| Coin | Adresse |
|------|---------|
| BTC | `bc1qnd599khdkv3v3npmj9ufxzf6h4fzanny2acwqr` |
| DOGE | `DL7tuiYCqm3xQjMDXChdxeQxqUGMACn1ZV` |
| ETH | `0x8A28fc47bFFFA03C8f685fa0836E2dBe1CA14F27` |

## Lizenz

Nicht-kommerzielle Lizenz v1.0 - siehe [LICENSE](LICENSE).
