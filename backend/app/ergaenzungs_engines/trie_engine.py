"""Wortvervollständigung: vollendet das gerade getippte Wort am Cursor.

Quelle sind die deutsche Häufigkeitsliste und das persönliche Wörterbuch
(gelernte Wörter zuerst). Der Vorschlag ist nur das fehlende Wortende (Suffix),
das an das bereits Getippte angehängt wird - so bleibt die Groß-/Kleinschreibung
des Präfix erhalten. Sofort, kein Sprachmodell nötig.
"""

from __future__ import annotations

import uuid
from typing import ClassVar

from app.lernen import frequenz, tokens, woerterbuch
from app.modelle.ergaenzung import ErgaenzungsAnfrage, ErgaenzungsModus, Vorschlag
from app.registry import ergaenzungs_engine

_MIN_PRAEFIX = 2


@ergaenzungs_engine
class TrieEngine:
    engine_id: ClassVar[str] = "trie"
    name: ClassVar[str] = "Wortvervollständigung"
    standard_an: ClassVar[bool] = True
    streaming: ClassVar[bool] = False

    def ist_verfuegbar(self) -> bool:
        return frequenz.verfuegbar()

    async def ergaenze(self, anfrage: ErgaenzungsAnfrage, kontext: str | None) -> list[Vorschlag]:
        teil = tokens.letztes_teilwort(anfrage.text_vor)
        if len(teil) < _MIN_PRAEFIX:
            return []
        teil_klein = teil.lower()
        top = max(anfrage.max_vorschlaege, 1)

        vorschlaege: list[Vorschlag] = []
        gesehen: set[str] = set()

        def aufnehmen(vollwort_klein: str, score: float) -> None:
            if vollwort_klein in gesehen or vollwort_klein == teil_klein:
                return
            suffix = vollwort_klein[len(teil_klein) :]
            if not suffix:
                return
            gesehen.add(vollwort_klein)
            vorschlaege.append(
                Vorschlag(
                    id=uuid.uuid4().hex,
                    text=suffix,
                    engine=self.engine_id,
                    score=score,
                    art=ErgaenzungsModus.WORT,
                )
            )

        # 1) Gelernte Wörter zuerst (hoher Score).
        profil = anfrage.profil_id or "standard"
        for wort, _h in woerterbuch.woerter_mit_praefix(teil_klein, profil_id=profil, limit=top):
            aufnehmen(wort.lower(), 0.95)

        # 2) Häufigkeitsliste, nach Rang absteigend gewichtet.
        treffer = frequenz.vervollstaendige(teil_klein, top=top + 3)
        for rang, (wort, _h) in enumerate(treffer):
            aufnehmen(wort, max(0.5, 0.85 - rang * 0.05))

        return vorschlaege[:top]
