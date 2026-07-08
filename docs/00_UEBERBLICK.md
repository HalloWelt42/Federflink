# Federflink - Ueberblick

## Zweck

Federflink ist ein lokaler Dienst fuer zwei Aufgaben rund um deutsche Texte:

1. **Rechtschreibung und Korrektur** - Tippfehler, Zeichensetzung, Grammatik.
2. **Textergaenzung** - eine Copilot-artige Vorschau der wahrscheinlichen
   Fortsetzung am Cursor, die man mit Tab uebernimmt und mit Esc verwirft.

Ein mitgeliefertes Browser-Plugin bringt beides in beliebige Eingabefelder und
Textbereiche. Die Vorschau wird nur angezeigt, nie automatisch eingefuegt.

## Leitgedanken

- **Server traegt die Sprachlogik, Clients bleiben duenn.** Alle Faehigkeiten
  liegen hinter einer klaren HTTP-API. Ein Client (Browser-Plugin, Editor, App)
  liest Kontext am Cursor, ruft die API und rendert die Vorschau - mehr nicht.
- **Fein steuerbar.** Engines, Schwellwerte, Entprellung, Modell und Profile sind
  zentral im Server konfigurierbar; pro Seite laesst sich alles ein-/ausschalten.
- **Modular.** Jede Faehigkeit ist eine austauschbare Engine hinter einem
  Protokoll (siehe [03_ENGINES.md](03_ENGINES.md)). Faellt eine Engine aus,
  liefern die schnellen weiter - nie ein Rueckschritt.
- **Lokal und privat.** Der Server lauscht nur auf localhost. Passwort-,
  Einmalcode- und Zahlungsfelder werden nie ausgelesen.
- **Lernfaehig.** Federflink lernt (1) allgemein den Wortschatz/Stil des Nutzers
  und (2) den Umfeld-Kontext des gerade geschriebenen Textes.

## Schichten

```
Browser-Plugin (duenn)            beliebiger weiterer Client
   |  HTTP (/api/complete, /api/spellcheck, /api/correct, /api/learn)
   v
FastAPI-Server (Federflink)
   |- Pruef-Engines:       Hunspell, LanguageTool (optional)
   |- Korrektur:           LLM-Umschreibung mit Schutznetzen
   |- Ergaenzungs-Engines: Trie, N-Gramm, LLM (kontextsensitiv)
   |- Dispatcher:          Instant-Vorschlag + LLM-Upgrade, Mischen/Ranking
   |- Lernen:              Woerterbuch, N-Gramm, Umfeld-Kontext (Embeddings)
   |- SQLite:              Einstellungen, Woerterbuch, N-Gramme, Kontext, Profile
   v
Lokales Sprachmodell (OpenAI-kompatibel: LM Studio / Ollama / llama.cpp)
```

## Was ist machbar

| Faehigkeit | Verfahren | Hinweis |
|---|---|---|
| Rechtschreibung (Wort) | Hunspell (spylls) + de_DE + persoenliches Woerterbuch | sofort, Pi-tauglich |
| Grammatik/Zeichensetzung | LanguageTool (optional, Java) | sehr gut, regelbasiert |
| Ganzsatz-Korrektur | Kleines LLM mit Schutznetzen | bewusste Aktion, kein Echtzeit |
| Wortergaenzung | Prefix-Trie ueber Haeufigkeiten + gelernte Woerter | sofort |
| Phrasen/naechstes Wort | N-Gramm, online lernend | sofort |
| Kontext-Ergaenzung | Kleines LLM + Umfeld-Kontext (Retrieval) | gestreamt, kontextsensitiv |
| Lernen (allgemein) | Woerterbuch + N-Gramm | wirkt sofort |
| Lernen (Umfeld) | Embeddings + Vektorsuche in SQLite | eigenstaendig, keine Fremd-App |

## Weiterlesen

- [01_ARCHITEKTUR.md](01_ARCHITEKTUR.md) - Komponenten und Datenfluss
- [02_API.md](02_API.md) - vollstaendige HTTP-API (Integrationsvertrag)
- [03_ENGINES.md](03_ENGINES.md) - eigene Engine hinzufuegen
- [04_LERNEN.md](04_LERNEN.md) - Lernmodell
- [05_PROFILE_UND_KONFIG.md](05_PROFILE_UND_KONFIG.md) - Profile und Einstellungen
- [06_BROWSER_PLUGIN.md](06_BROWSER_PLUGIN.md) - Aufbau der Erweiterung
- [07_CLIENT_INTEGRATION.md](07_CLIENT_INTEGRATION.md) - in eigene Apps einbinden
- [08_DEPLOYMENT_PI.md](08_DEPLOYMENT_PI.md) - Betrieb auf dem Pi5
- [09_MODELLE.md](09_MODELLE.md) - empfohlene Modelle
