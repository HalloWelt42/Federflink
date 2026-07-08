# Federflink - Eigene Engine hinzufügen

## Prinzip

Eine Engine = eine Datei im passenden Paket. Der Import beim Start löst den
Dekorator aus, der Capabilities-Endpunkt macht sie bekannt. Kein weiterer Code
im Aufrufer nötig.

## Prüf-Engine (Rechtschreibung/Grammatik)

Vertrag: `app/schnittstellen/pruef_engine.py`

```python
from typing import ClassVar
from app.registry import pruef_engine
from app.modelle.pruefung import Befund, BefundArt

@pruef_engine
class MeineEngine:
    engine_id: ClassVar[str] = "meine"
    name: ClassVar[str] = "Meine Engine"
    standard_an: ClassVar[bool] = True

    def ist_verfuegbar(self) -> bool:
        return True

    def pruefe(self, text: str, sprache: str) -> list[Befund]:
        return []
```

Datei ablegen unter `app/pruef_engines/meine_engine.py`.

## Ergänzungs-Engine (Textvervollständigung)

Vertrag: `app/schnittstellen/ergaenzungs_engine.py`. Analog, mit
`async def ergaenze(self, anfrage, kontext) -> list[Vorschlag]` und
`streaming: ClassVar[bool]`. Datei unter `app/ergaenzungs_engines/`.
