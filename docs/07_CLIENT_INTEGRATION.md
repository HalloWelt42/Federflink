# Federflink - In eigene Anwendungen einbinden

> Der Leitfaden fuer Programme und andere KI-Modelle. Wird mit den API-Phasen
> vervollstaendigt; das Grundmuster steht bereits.

## Grundmuster (jeder Client)

1. Beim Start `GET /api/capabilities` lesen und daraus Bedienelemente ableiten
   (verfuegbare Engines, Modi, Profile, Grenzen). Nichts fest verdrahten.
2. Fuer Rechtschreibung: Text an `POST /api/spellcheck` senden, Funde markieren.
3. Fuer Ergaenzung: Kontext um den Cursor an `POST /api/complete` senden, den
   ersten Vorschlag als Vorschau zeigen, per SSE auf ein besseres Upgrade warten.
4. Nur bei Uebernahme `POST /api/learn` senden (fuer das Lernen).

## Minimalbeispiel (Rechtschreibung)

```bash
curl -s http://localhost:8500/api/health
```

Weitere Endpunkte und vollstaendige Beispiele: [02_API.md](02_API.md).
Die maschinenlesbare Spezifikation liegt unter `/openapi.json`.
