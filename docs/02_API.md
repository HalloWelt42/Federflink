# Federflink - HTTP-API

Basis-Präfix: `/api`. Alle Antworten sind JSON (UTF-8). Der Server lauscht nur
auf localhost. Eine maschinenlesbare Fassung liegt unter `/openapi.json`
(interaktiv unter `/docs`). JSON-Schlüssel sind bewusst deutsch und ASCII.

## Fehlerformat

Jeder Fehler kommt einheitlich, zusätzlich im Header `X-Request-Id`:

```json
{ "fehler": { "code": "engine_nicht_verfuegbar", "meldung": "...", "details": {}, "request_id": "uuid" } }
```

Stabile Codes: `eingabe_ungueltig` (422), `engine_nicht_verfuegbar` (409),
`llm_nicht_erreichbar` (502), `limit_ueberschritten` (413),
`modul_unbekannt` (404), `intern` (500).

---

## GET /api/health

```json
{ "status": "ok", "name": "Federflink", "version": "0.1.0" }
```

## GET /api/capabilities

Selbstauskunft - Clients bauen ihre Bedienelemente daraus.

```json
{
  "version": "0.1.0",
  "name": "Federflink",
  "pruef_engines":       [{ "id": "hunspell", "name": "Hunspell (Rechtschreibung)", "aktiv": true, "standard_an": true, "streaming": false }],
  "ergaenzungs_engines": [{ "id": "llm", "name": "Sprachmodell (kontextsensitiv)", "aktiv": true, "standard_an": true, "streaming": true }],
  "modi": ["wort", "phrase", "satz"],
  "profile": [{ "id": "standard", "name": "Standard", "sprache": "de", "beschreibung": "..." }],
  "grenzen": { "budget_vor": 800, "budget_nach": 200, "debounce_ms": 150, "min_zeichen": 3, "max_vorschlaege": 3, "max_text_zeichen": 20000 },
  "funktionen": { "sse": true, "lernen": true, "teil_uebernahme": true },
  "llm": { "erreichbar": true, "url": "http://localhost:1234", "modelle": ["..."] }
}
```

## GET /api/models

`{ "erreichbar": true, "url": "http://localhost:1234", "modelle": ["..."] }`

## GET /api/status

Lernstand und Telemetrie (Admin-Transparenz).

```json
{ "woerter": 42, "ngramme": 128, "kontext": 17,
  "annahmen": [{ "engine": "trie", "uebernahmen": 30, "ablehnungen": 3 }] }
```

---

## POST /api/spellcheck

Rechtschreib-/Grammatikprüfung. Request:

```json
{ "text": "Das ist ein Fehlar.", "sprache": "de-DE", "profil_id": "standard", "engines": null }
```

`engines: null` = alle standardmäßig aktiven Prüf-Engines. Antwort:

```json
{ "befunde": [ { "offset": 12, "laenge": 6, "art": "rechtschreibung",
                 "meldung": "Mögliche falsche Schreibweise: Fehlar",
                 "regel_id": null, "vorschlaege": ["Fehler", "Fehlart"], "engine": "hunspell" } ],
  "engines": ["hunspell"], "dauer_ms": 8 }
```

`art` ∈ `rechtschreibung | grammatik | zeichensetzung | stil | tippfehler`.
`offset`/`laenge` beziehen sich auf den gesendeten Text (Zeichen). Wörter aus dem
persönlichen Wörterbuch des Profils werden nicht gemeldet.

## POST /api/correct

Neuronale Ganzsatz-Korrektur (nur Form, nie Inhalt). Request:
`{ "text": "...", "profil_id": null, "modell": null }`. Antwort:

```json
{ "original": "...", "korrigiert": "...", "engine": "llm", "veraendert": true }
```

Bei fehlendem/langsamem Modell oder verdächtiger Abweichung wird der Originaltext
unverändert zurückgegeben (`veraendert: false`).

## POST /api/complete

Textergänzung am Cursor. Request:

```json
{
  "request_id": "c7f2", "sitzung_id": "",
  "text_vor": "Text bis zum Cursor", "text_nach": "Text nach dem Cursor",
  "cursor": { "im_wort": false, "am_zeilenende": true },
  "modus": "phrase", "engines": null, "profil_id": "standard",
  "seite": { "host": "mail.example.org", "feld_art": "textarea", "sprach_hinweis": "de" },
  "locale": "de-DE", "max_vorschlaege": 3, "kontext_hash": ""
}
```

Zwei Betriebsarten je nach `Accept`-Header:

### application/json (Vorgabe) - nur Instant-Vorschlag

```json
{ "request_id": "c7f2", "erzeugt_ms": 6,
  "vorschlaege": [ { "id": "…", "text": "el", "engine": "trie", "score": 0.85,
                     "art": "wort", "ersetze_vor": 0, "anzeige_text": null, "final": true } ],
  "upgrade_aussteht": true, "engine_status": { "trie": "ok", "ngram": "ok" } }
```

Wichtig: `text` ist der einzufügende String. Bei der Trie-Engine ist das nur das
fehlende Wortende (Suffix), das direkt an den Cursor angehängt wird; die N-Gramm-/
LLM-Engine bringen ein führendes Leerzeichen bereits mit, wo nötig.

### text/event-stream - Progressive Enhancement (empfohlen für Live-Tippen)

```
event: instant
data: {"request_id":"c7f2","vorschlaege":[{…trie/ngram…}],"engine_status":{…},"upgrade_aussteht":true}

event: token
data: {"request_id":"c7f2","id":"llm","delta":"vielen "}

event: upgrade
data: {"request_id":"c7f2","vorschlaege":[{…llm, final:true…}]}

event: done
data: {"request_id":"c7f2"}
```

Der Client zeigt den `instant`-Vorschlag sofort und ersetzt ihn beim `upgrade`
(sofern `request_id` noch aktuell und der Kontext unverändert ist). Bricht der
Client die Verbindung ab, endet die Generierung serverseitig.

## POST /api/learn

Lernsignal bei Übernahme (oder Ablehnung). Request:

```json
{ "uebernommen_text": "el", "uebernommen_engine": "trie", "teil_uebernahme": false,
  "profil_id": "standard", "seite": { "host": "…", "feld_art": "textarea", "sprach_hinweis": "de" },
  "text_vor": "Das ist ein Beispi" }
```

`text_vor` NUR senden, wenn der Nutzer pro Seite "hier verbessern" erlaubt hat
(Datenschutz-Gate). Ist es gesetzt, werden N-Gramme aus dem Umfeld und - bei
mehrwortigen Übernahmen - eine eingebettete Kontext-Passage gelernt. Unbekannte
Wörter wandern immer ins persönliche Wörterbuch. Antwort:
`{ "gelernt": true, "hinweis": "..." }`.

---

## Wörterbuch

- `GET /api/woerterbuch?profil_id=standard` -> `{ "woerter": [{ "wort","profil_id","haeufigkeit","quelle" }], "anzahl": 42 }`
- `POST /api/woerterbuch` `{ "wort": "Federflink", "profil_id": "standard" }` -> `WortEintrag`
- `DELETE /api/woerterbuch` `{ "wort": "Federflink", "profil_id": "standard" }` -> `{ "entfernt": true }`

## Profile

- `GET /api/profiles` -> Liste von `{ id,name,sprache,beschreibung,stil_prompt,host_muster,aktiv,eingebaut }`
- `POST /api/profiles` `{ id,name,sprache?,beschreibung?,stil_prompt?,host_muster? }` -> `Profil`
- `DELETE /api/profiles/{id}` -> `{ "entfernt": true }` (eingebaute Profile sind geschützt)
- `GET /api/profiles/host?host=mail.example.org` -> `{ "profil_id": "email-de" | null }`
