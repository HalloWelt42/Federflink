# Federflink - Profile und Konfiguration

## Profile

Ein Profil buendelt Ton/Stil (System-Hinweis fuer das LLM), ein eigenes
Woerterbuch und einen eigenen Umfeld-Kontext. Eingebaut: `standard`, `email-de`,
`chat-de`. Weitere lassen sich im UI anlegen. Host-Muster ordnen Seiten
automatisch einem Profil zu (z. B. Mail-Dienste -> `email-de`).

## Konfiguration

- **Serverseitig (zentral, im UI aenderbar):** aktive Engines, Schwellwerte,
  Entprellung, Kontext-Budget, Modell und Endpunkt, Ranking-Gewichte, Profile.
  Liegt in der `settings`-Tabelle; Standardwerte in `backend/app/config.py`.
- **Clientseitig (Browser-Erweiterung):** globaler Schalter, pro-Seite an/aus,
  Profil-Wahl je Seite, Tastenbelegung, Anzeige-Modus. Liegt in `chrome.storage.sync`.

Trennprinzip: Sprache/Modell/Ranking = Server; Einwilligung/Tasten/lokale Optik = Client.
