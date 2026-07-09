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

- `input`/`textarea` am Zeilenende: Inline-Geistertext über einen Overlay-Mirror
  (Shadow-DOM), der Text und Stil des Feldes spiegelt.
- `contenteditable` (Discord/Twitch u. a.) und mid-line-Fälle: grauer Geistertext
  als Overlay direkt am Cursor - ohne den Editor-DOM anzufassen. Er sitzt auf der
  Cursor-Zeile, daher kein Problem bei Feldern am unteren Bildrand.

## Bedienung

- Tab = übernehmen, Ctrl/Alt+Pfeil rechts = ein Wort übernehmen, Esc = verwerfen.
- Globaler Schalter und pro-Seite an/aus, damit nichts zugespammt wird.

## Datenschutz

Niemals Passwort-, Einmalcode- oder Zahlungsfelder (auch nicht Felder im selben
Formular wie ein Passwort). Nur Host statt voller URL. Nur localhost-Transport.
