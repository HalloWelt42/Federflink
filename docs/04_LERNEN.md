# Federflink - Lernen

Federflink lernt auf zwei Ebenen; beides wird ueber `POST /api/learn` gespeist.

## Stufe 1 - allgemein

- **Persoenliches Woerterbuch** (`woerter`): Woerter, die der Nutzer schreibt oder
  uebernimmt, werden gezaehlt. Sie fliessen in den Trie und heben Hunspell-Warnungen
  fuer Eigennamen/Fachbegriffe auf.
- **N-Gramm-Haeufigkeiten** (`ngramme`): bei jeder Uebernahme werden die
  vorangehenden Woerter -> Folgewort gezaehlt und sagen naechste Woerter voraus.

Aktualisiert ueber `POST /api/learn`.

## Stufe 2 - Umfeld-Kontext (eigenstaendig)

- Akzeptierte Passagen werden ueber den lokalen Embedding-Endpunkt eingebettet und
  als Vektor in `kontext_passagen` (SQLite) abgelegt - kein externer Dienst.
- Bei einer Ergaenzung werden aehnliche Passagen des passenden Profils gesucht und
  in den LLM-Prompt gegeben, sodass Vorschlaege zu Stil und Inhalt passen.
- Rohtext wird nur gelernt, wenn pro Seite "hier verbessern" aktiv ist.
