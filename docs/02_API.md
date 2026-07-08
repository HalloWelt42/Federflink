# Federflink - HTTP-API

Basis-Praefix: `/api`. Alle Antworten sind JSON (UTF-8). Der Server lauscht nur
auf localhost. Eine maschinenlesbare Fassung liegt unter `/openapi.json`
(interaktiv unter `/docs`).

## Fehlerformat

Jeder Fehler kommt einheitlich:

```json
{ "fehler": { "code": "modul_unbekannt", "meldung": "...", "details": {}, "request_id": "uuid" } }
```

Der Header `X-Request-Id` traegt dieselbe Kennung. Stabile Codes u. a.:
`eingabe_ungueltig` (422), `engine_nicht_verfuegbar` (409),
`llm_nicht_erreichbar` (502), `limit_ueberschritten` (413), `intern` (500).

## GET /api/health

Schnelle Lebendpruefung.

```json
{ "status": "ok", "name": "Federflink", "version": "0.1.0" }
```

## GET /api/capabilities

Selbstauskunft. Clients bauen ihre Bedienelemente daraus - nichts ist im Client
fest verdrahtet.

```json
{
  "version": "0.1.0",
  "name": "Federflink",
  "pruef_engines": [ { "id": "hunspell", "name": "Hunspell", "aktiv": true, "standard_an": true, "streaming": false } ],
  "ergaenzungs_engines": [ { "id": "ngram", "name": "N-Gramm", "aktiv": true, "standard_an": true, "streaming": false } ],
  "modi": ["wort", "phrase", "satz"],
  "profile": [ { "id": "standard", "name": "Standard", "sprache": "de", "beschreibung": "..." } ],
  "grenzen": { "budget_vor": 800, "budget_nach": 200, "debounce_ms": 150, "min_zeichen": 3, "max_vorschlaege": 3, "max_text_zeichen": 20000 },
  "funktionen": { "sse": true, "lernen": true, "teil_uebernahme": true },
  "llm": null
}
```

## Noch nicht dokumentiert (kommen mit den Ausbaustufen)

- `POST /api/spellcheck` - Rechtschreib-/Grammatik-Funde (Phase 1)
- `POST /api/correct` - Ganzsatz-Korrektur mit Diff (Phase 1)
- `POST /api/complete` - Textergaenzung, SSE-Progressive-Enhancement (Phase 2/3)
- `POST /api/learn` - Lernsignal bei Uebernahme (Phase 2)
- `GET/PUT /api/config` - zentrale Einstellungen (Phase 3)
- `GET /api/models` - geladene Sprachmodelle (Phase 3)
- `GET/POST/PUT/DELETE /api/profiles`, `GET/POST/DELETE /api/woerterbuch` (Phase 4)

Die Request-/Response-Schemas dieser Endpunkte stehen bereits als Pydantic-Modelle
in `backend/app/modelle/` und werden hier bei Fertigstellung je Phase ergaenzt.
