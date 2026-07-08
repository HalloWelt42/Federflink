# Federflink - Browser-Erweiterung

Zeigt in beliebigen Eingabefeldern eine Copilot-artige Vorschau: Inline-Geistertext
in `input`/`textarea` (am Zeilenende), sonst eine schwebende Pille. **Tab** uebernimmt,
**Esc** verwirft. Nichts wird automatisch eingefuegt.

## Laden (Chrome / Chromium, entpackt)

1. Federflink-Server starten: im Projektwurzelordner `./start.sh start`
   (Server auf `http://localhost:8500`).
2. `chrome://extensions` oeffnen, oben rechts **Entwicklermodus** einschalten.
3. **Entpackte Erweiterung laden** und diesen Ordner (`extension/`) waehlen.
4. Auf einer Seite in ein Textfeld tippen - nach kurzer Pause erscheint die Vorschau.

## Bedienung

- **Tab** - Vorschlag ganz uebernehmen
- **Strg/Alt + Pfeil rechts** - nur das naechste Wort uebernehmen
- **Esc** - Vorschlag verwerfen
- **Alt+Shift+F** - Federflink global ein-/ausschalten (Kurzbefehl)
- Klick auf das Symbol: globaler Schalter, pro-Seite-Schalter, Profilwahl, "hier verbessern"

## Datenschutz

- Der Server laeuft nur lokal; die Erweiterung spricht ausschliesslich mit ihm.
- Passwort-, Einmalcode- und Zahlungsfelder (sowie Felder im selben Formular wie ein
  Passwort) werden nie ausgelesen.
- Umgebungstext wird nur gelernt, wenn pro Seite "hier verbessern" aktiv ist.

## Aufbau (drei Schichten)

- `src/content/assistant.js` (isolierte Welt) - Feldbeobachtung, Kontext am Cursor,
  Entprellung, Geistertext/Pille, Tastensteuerung.
- `src/content/ghost-inject.js` (Seitenwelt) - robustes Einfuegen in Framework-Felder.
- `src/background/service-worker.js` - Netzwerk (SSE), Lernsignale, Zustand, Kurzbefehl, Badge.
- `src/popup/` und `src/pages/` - Popup und Einstellungsseite.
- `shared/defaults.js` - gemeinsame Standardwerte/Helfer.

## Anderer Server-Host (z. B. Raspberry Pi)

Die Server-URL in den Einstellungen setzen und in `manifest.json` unter
`host_permissions` die Adresse ergaenzen (z. B. `http://192.168.178.49:8500/*`),
danach die Erweiterung neu laden.
