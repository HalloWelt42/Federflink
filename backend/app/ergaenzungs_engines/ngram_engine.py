"""Nächstes-Wort-/Phrasen-Vorhersage aus gelernten N-Grammen.

Greift, wenn der Cursor hinter einem Worttrenner steht (kein offenes Wort). Lernt
online: anfangs leer, wird mit jeder Übernahme besser. Kann mehrere Wörter als
Phrase vorschlagen, solange die Fortsetzung hinreichend belegt ist.
"""

from __future__ import annotations

import uuid
from typing import ClassVar

from app.lernen import ngramm_speicher, tokens
from app.modelle.ergaenzung import ErgaenzungsAnfrage, ErgaenzungsModus, Vorschlag
from app.registry import ergaenzungs_engine


@ergaenzungs_engine
class NgramEngine:
    engine_id: ClassVar[str] = "ngram"
    name: ClassVar[str] = "Nächstes Wort (N-Gramm)"
    standard_an: ClassVar[bool] = True
    streaming: ClassVar[bool] = False

    def ist_verfuegbar(self) -> bool:
        return True

    async def ergaenze(self, anfrage: ErgaenzungsAnfrage, kontext: str | None) -> list[Vorschlag]:
        # Nur wenn kein offenes Wort am Cursor steht (sonst ist die Trie-Engine zuständig).
        if tokens.letztes_teilwort(anfrage.text_vor):
            return []
        vorher = tokens.woerter(anfrage.text_vor)
        if not vorher:
            return []

        profil = anfrage.profil_id or "standard"
        vorschlaege: list[Vorschlag] = []

        # Führendes Leerzeichen ergänzen, falls der bisherige Text nicht schon mit
        # einem Trenner endet (z. B. nach Satzzeichen ohne Leerzeichen).
        trenner = "" if anfrage.text_vor.endswith((" ", "\n", "\t")) else " "

        if anfrage.modus in (ErgaenzungsModus.PHRASE, ErgaenzungsModus.SATZ):
            phrase = ngramm_speicher.vorhersage_phrase(vorher, profil_id=profil)
            if phrase:
                vorschlaege.append(
                    Vorschlag(
                        id=uuid.uuid4().hex,
                        text=trenner + " ".join(phrase),
                        engine=self.engine_id,
                        score=0.8,
                        art=ErgaenzungsModus.PHRASE,
                    )
                )

        for rang, (wort, _h) in enumerate(
            ngramm_speicher.vorhersage_naechstes(vorher, profil_id=profil, top=anfrage.max_vorschlaege)
        ):
            vorschlaege.append(
                Vorschlag(
                    id=uuid.uuid4().hex,
                    text=trenner + wort,
                    engine=self.engine_id,
                    score=max(0.5, 0.75 - rang * 0.05),
                    art=ErgaenzungsModus.WORT,
                )
            )

        # Doppelte (Phrase beginnt mit demselben Wort) grob entdoppeln.
        gesehen: set[str] = set()
        einzigartig: list[Vorschlag] = []
        for v in vorschlaege:
            schluessel = v.text.strip().lower()
            if schluessel in gesehen:
                continue
            gesehen.add(schluessel)
            einzigartig.append(v)
        return einzigartig[: anfrage.max_vorschlaege]
