# Federflink - Lernen

Federflink lernt auf zwei Ebenen; beides wird über `POST /api/learn` gespeist.

## Stufe 1 - allgemein

- **Persönliches Wörterbuch** (`woerter`): Wörter, die der Nutzer schreibt oder
  übernimmt, werden gezählt. Sie fließen in den Trie und heben Hunspell-Warnungen
  für Eigennamen/Fachbegriffe auf.
- **N-Gramm-Häufigkeiten** (`ngramme`): bei jeder Übernahme werden die
  vorangehenden Wörter -> Folgewort gezählt und sagen nächste Wörter voraus.

Aktualisiert über `POST /api/learn`.

## Stufe 2 - Umfeld-Kontext (eigenständig)

- Akzeptierte Passagen werden über den lokalen Embedding-Endpunkt eingebettet und
  als Vektor in `kontext_passagen` (SQLite) abgelegt - kein externer Dienst.
- Bei einer Ergänzung werden ähnliche Passagen des passenden Profils gesucht und
  in den LLM-Prompt gegeben, sodass Vorschläge zu Stil und Inhalt passen.
- Rohtext wird nur gelernt, wenn pro Seite "hier verbessern" aktiv ist.
