# Federflink - Überblick

## Zweck

Federflink ist ein lokaler Dienst für zwei Aufgaben rund um deutsche Texte:

1. **Rechtschreibung und Korrektur** - Tippfehler, Zeichensetzung, Grammatik.
2. **Textergänzung** - eine Copilot-artige Vorschau der wahrscheinlichen
   Fortsetzung am Cursor, die man mit Tab übernimmt und mit Esc verwirft.

Ein mitgeliefertes Browser-Plugin bringt beides in beliebige Eingabefelder und
Textbereiche. Die Vorschau wird nur angezeigt, nie automatisch eingefügt.

## Leitgedanken

- **Server trägt die Sprachlogik, Clients bleiben dünn.** Alle Fähigkeiten
  liegen hinter einer klaren HTTP-API. Ein Client (Browser-Plugin, Editor, App)
  liest Kontext am Cursor, ruft die API und rendert die Vorschau - mehr nicht.
- **Fein steuerbar.** Engines, Schwellwerte, Entprellung, Modell und Profile sind
  zentral im Server konfigurierbar; pro Seite lässt sich alles ein-/ausschalten.
- **Modular.** Jede Fähigkeit ist eine austauschbare Engine hinter einem
  Protokoll (siehe [03_ENGINES.md](03_ENGINES.md)). Fällt eine Engine aus,
  liefern die schnellen weiter - nie ein Rückschritt.
- **Lokal und privat.** Der Server lauscht nur auf localhost. Passwort-,
  Einmalcode- und Zahlungsfelder werden nie ausgelesen.
- **Lernfähig.** Federflink lernt (1) allgemein den Wortschatz/Stil des Nutzers
  und (2) den Umfeld-Kontext des gerade geschriebenen Textes.

## Schichten

```
Browser-Plugin (dünn)            beliebiger weiterer Client
   |  HTTP (/api/complete, /api/spellcheck, /api/correct, /api/learn)
   v
FastAPI-Server (Federflink)
   |- Prüf-Engines:       Hunspell, LanguageTool (optional)
   |- Korrektur:           LLM-Umschreibung mit Schutznetzen
   |- Ergänzungs-Engines: Trie, N-Gramm, LLM (kontextsensitiv)
   |- Dispatcher:          Instant-Vorschlag + LLM-Upgrade, Mischen/Ranking
   |- Lernen:              Wörterbuch, N-Gramm, Umfeld-Kontext (Embeddings)
   |- SQLite:              Einstellungen, Wörterbuch, N-Gramme, Kontext, Profile
   v
Lokales Sprachmodell (OpenAI-kompatibel: LM Studio / Ollama / llama.cpp)
```

## Was ist machbar

| Fähigkeit | Verfahren | Hinweis |
|---|---|---|
| Rechtschreibung (Wort) | Hunspell (spylls) + de_DE + persönliches Wörterbuch | sofort, Pi-tauglich |
| Grammatik/Zeichensetzung | LanguageTool (optional, Java) | sehr gut, regelbasiert |
| Ganzsatz-Korrektur | Kleines LLM mit Schutznetzen | bewusste Aktion, kein Echtzeit |
| Wortergänzung | Prefix-Trie über Häufigkeiten + gelernte Wörter | sofort |
| Phrasen/nächstes Wort | N-Gramm, online lernend | sofort |
| Kontext-Ergänzung | Kleines LLM + Umfeld-Kontext (Retrieval) | gestreamt, kontextsensitiv |
| Lernen (allgemein) | Wörterbuch + N-Gramm | wirkt sofort |
| Lernen (Umfeld) | Embeddings + Vektorsuche in SQLite | eigenständig, keine Fremd-App |

## Weiterlesen

- [01_ARCHITEKTUR.md](01_ARCHITEKTUR.md) - Komponenten und Datenfluss
- [02_API.md](02_API.md) - vollständige HTTP-API (Integrationsvertrag)
- [03_ENGINES.md](03_ENGINES.md) - eigene Engine hinzufügen
- [04_LERNEN.md](04_LERNEN.md) - Lernmodell
- [05_PROFILE_UND_KONFIG.md](05_PROFILE_UND_KONFIG.md) - Profile und Einstellungen
- [06_BROWSER_PLUGIN.md](06_BROWSER_PLUGIN.md) - Aufbau der Erweiterung
- [07_CLIENT_INTEGRATION.md](07_CLIENT_INTEGRATION.md) - in eigene Apps einbinden
- [08_DEPLOYMENT_PI.md](08_DEPLOYMENT_PI.md) - Betrieb auf dem Pi5
- [09_MODELLE.md](09_MODELLE.md) - empfohlene Modelle
