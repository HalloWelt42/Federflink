# Federflink - Browser-Plugin

Die Erweiterung liegt unter `extension/` (Manifest V3, reines JavaScript). Laden
und Bedienung: siehe `extension/README.md`.

## Aufbau (drei Schichten)

- **MAIN-World-Skript** (`ghost-inject.js`): nur beim Übernehmen - robustes
  Einfügen in Framework-Felder (React/Vue) über den nativen value-Setter.
- **ISOLATED Content-Skript** (`assistant.js`): Fokus/Eignung, Kontext-Extraktion,
  Entprellung, Rendering, Tastensteuerung, Reconcile.
- **Service-Worker**: besitzt das Netzwerk (fetch + SSE), leitet Frames an das
  Content-Skript, cached `capabilities`, ruft `/api/learn`, zweites Datenschutz-Gate.

## Anzeige (hybrid)

- `input`/`textarea`: Inline-Geistertext über einen Overlay-Mirror (Shadow-DOM),
  nur am Zeilenende; sonst Pille.
- `contenteditable`/komplexe Editoren: schwebende Pille am Cursor.

## Bedienung

- Tab = übernehmen, Ctrl/Alt+Pfeil rechts = ein Wort übernehmen, Esc = verwerfen.
- Globaler Schalter und pro-Seite an/aus, damit nichts zugespammt wird.

## Datenschutz

Niemals Passwort-, Einmalcode- oder Zahlungsfelder (auch nicht Felder im selben
Formular wie ein Passwort). Nur Host statt voller URL. Nur localhost-Transport.
