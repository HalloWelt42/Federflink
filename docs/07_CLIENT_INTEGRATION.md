# Federflink - In eigene Anwendungen einbinden

Dieser Leitfaden richtet sich an Programme und andere KI-Modelle, die Federflink
in einen Editor, eine App oder ein Plugin einbinden. Der vollständige Vertrag
steht in [02_API.md](02_API.md); hier stehen die Rezepte.

## Grundregeln

1. Beim Start `GET /api/capabilities` lesen und daraus die Bedienelemente ableiten
   (verfügbare Engines, Modi, Profile, Grenzen). Nichts fest verdrahten.
2. Der Server trägt die Sprachlogik. Der Client liest nur Kontext am Cursor,
   entprellt, ruft die API und zeigt die Vorschau. Nie automatisch einfügen.
3. Passwort-/Einmalcode-/Zahlungsfelder niemals auslesen. Umgebungstext (`text_vor`
   bei `/learn`) nur mit ausdrücklicher Einwilligung senden.

## Rechtschreibung

```bash
curl -s http://localhost:8500/api/spellcheck \
  -H 'Content-Type: application/json' \
  -d '{"text":"Das ist ein Fehlar.","profil_id":"standard"}'
```

Die `befunde` tragen `offset`/`laenge` (Zeichen im gesendeten Text) und
`vorschlaege`. Markiere die Stellen und biete die Vorschläge an; beim Übernehmen
den Bereich `text[offset:offset+laenge]` durch den Vorschlag ersetzen.

## Ganzsatz-Korrektur

```bash
curl -s http://localhost:8500/api/correct \
  -H 'Content-Type: application/json' -d '{"text":"ich glab das stimt nich"}'
```

Zeige `original` vs. `korrigiert` als Diff und lass den Nutzer entscheiden.

## Ergänzung (empfohlen: SSE)

Sende Kontext um den Cursor, zeige den `instant`-Vorschlag sofort, ersetze ihn beim
`upgrade`. Minimaler JavaScript-Konsument:

```js
async function ergaenze(textVor, textNach, aufVorschlag, signal) {
  const resp = await fetch('http://localhost:8500/api/complete', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json', Accept: 'text/event-stream' },
    body: JSON.stringify({
      request_id: String(Date.now()),
      text_vor: textVor.slice(-800), text_nach: textNach.slice(0, 200),
      modus: 'phrase', profil_id: 'standard',
      seite: { host: location.hostname, feld_art: 'textarea', sprach_hinweis: 'de' },
    }),
    signal,
  })
  const leser = resp.body.getReader(); const dec = new TextDecoder(); let puffer = ''
  for (;;) {
    const { done, value } = await leser.read(); if (done) break
    puffer += dec.decode(value, { stream: true })
    let i; while ((i = puffer.indexOf('\n\n')) >= 0) {
      const roh = puffer.slice(0, i); puffer = puffer.slice(i + 2)
      let ev = 'message', data = ''
      for (const z of roh.split('\n')) {
        if (z.startsWith('event:')) ev = z.slice(6).trim()
        else if (z.startsWith('data:')) data += z.slice(5).trim()
      }
      if ((ev === 'instant' || ev === 'upgrade') && data) {
        const obj = JSON.parse(data)
        if (obj.vorschlaege && obj.vorschlaege[0]) aufVorschlag(obj.vorschlaege[0])
      }
    }
  }
}
```

Ohne Streaming: dieselbe Anfrage mit `Accept: application/json` liefert nur den
Instant-Vorschlag (Trie/N-Gramm), ohne LLM-Upgrade.

**Einfügen:** `vorschlag.text` genau am Cursor einsetzen. Es ist entweder ein
Wortsuffix (direkt anhängen) oder bringt sein führendes Leerzeichen mit - in
beiden Fällen einfach `text_vor + vorschlag.text + text_nach`.

## Lernen

Beim Übernehmen ein Signal senden, damit Federflink besser wird:

```bash
curl -s http://localhost:8500/api/learn -H 'Content-Type: application/json' \
  -d '{"uebernommen_text":"el","uebernommen_engine":"trie","text_vor":"Das ist ein Beispi","profil_id":"standard","seite":{"host":"example.org","feld_art":"textarea","sprach_hinweis":"de"}}'
```

`text_vor` nur mit Einwilligung mitsenden (Umfeld-Kontext, Stufe 2).

## CORS

Der Server erlaubt den Vite-Frontend-Ursprung und Erweiterungs-Ursprünge
(`chrome-extension://…`). Aus einer beliebigen Webseite heraus ist der direkte
Zugriff durch CORS gesperrt - dort über einen eigenen Hintergrundprozess
(Service-Worker) gehen, dessen Anfragen nicht der Seiten-CORS unterliegen. Genau
so macht es die mitgelieferte Browser-Erweiterung (siehe [06_BROWSER_PLUGIN.md](06_BROWSER_PLUGIN.md)).
