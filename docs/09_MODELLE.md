# Federflink - Empfohlene Modelle

Federflink spricht jeden OpenAI-kompatiblen Server an (LM Studio, Ollama,
llama.cpp); das Modell ist frei wählbar.

## Ergänzung (Chat/Completion)

Kleine, mehrsprachige Modelle mit guter deutscher Ausgabe, quantisiert (Q4):

| Modell | Größe | Eignung |
|---|---|---|
| Qwen2.5-1.5B-Instruct | ~1 GB | schnell, solide - guter Standard auf dem Pi |
| Qwen2.5-3B-Instruct | ~2 GB | besser, etwas langsamer |
| Llama-3.2-1B / 3B-Instruct | ~1-2 GB | Alternative |
| Gemma-2-2B-Instruct | ~1.6 GB | Alternative |

Für kurze Ergänzungen (wenige Wörter bis ein Satz) reichen kleine Modelle;
Ausgabe wird gestreamt, damit die Vorschau schnell erscheint.

**Wichtig:** Ein normales Instruct-Modell verwenden, KEIN Reasoning-Modell.
Reasoning-Modelle geben zuerst längeres Nachdenken aus; bei den kurzen
Token-Grenzen der Ergänzung kommt dann keine brauchbare Fortsetzung an.
Federflink filtert zwar `<think>`-Blöcke heraus, doch die eigentliche Antwort
bleibt bei reinen Reasoning-Modellen oft aus. Ist nur ein Reasoning-Modell
geladen, funktionieren Rechtschreibung und Trie/N-Gramm weiter - nur der
LLM-Vorschlag bleibt leer.

## Embeddings (Umfeld-Kontext, Phase 4)

| Modell | Hinweis |
|---|---|
| bge-m3 | mehrsprachig, empfohlen |

## Auswahl im Betrieb

Das aktive Modell wird über die zentrale Konfiguration bzw. `GET /api/models`
gewählt. Federflink nutzt bevorzugt das bereits geladene Modell, um kein anderes
per JIT nachzuladen.
