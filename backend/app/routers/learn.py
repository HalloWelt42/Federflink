"""Endpunkt Lernsignal: verarbeitet uebernommene Vorschlaege (Lernen Stufe 1).

- Unbekannte Woerter wandern ins persoenliche Woerterbuch (Hunspell kennt sie dann).
- N-Gramme werden aus dem Umfeld (Text vor dem Cursor + Uebernahme) gelernt,
  aber nur wenn der Client den Kontext mitschickt (Datenschutz-Gate 'hier verbessern').
- Jede Uebernahme/Ablehnung wird fuer die Statusansicht gezaehlt.
"""

from __future__ import annotations

from app.lernen import ngramm_speicher, telemetrie, tokens, woerterbuch
from app.modelle.ergaenzung import LernAnfrage, LernAntwort
from app.pruef_engines import hunspell_engine
from fastapi import APIRouter

router = APIRouter(tags=["Lernen"])


@router.post("/learn")
def learn(anfrage: LernAnfrage) -> LernAntwort:
    profil = anfrage.profil_id or "standard"
    roh = anfrage.uebernommen_text  # Rohform: Vorschlag kann Suffix oder fuehrendes Leerzeichen tragen
    uebernommen = roh.strip()

    if not uebernommen:
        telemetrie.erfasse(
            engine=anfrage.uebernommen_engine or "",
            art="ablehnung",
            profil_id=profil,
            host=anfrage.seite.host,
        )
        return LernAntwort(gelernt=False, hinweis="Nichts uebernommen.")

    # Unbekannte Woerter ins persoenliche Woerterbuch (nicht die Allerweltswoerter).
    for wort in tokens.woerter(uebernommen):
        if len(wort) < 3:
            continue
        if hunspell_engine.kennt_wort(wort) is False:
            woerterbuch.hinzufuegen(wort, profil_id=profil, quelle="gelernt")

    # N-Gramme lernen. WICHTIG: direkt aneinanderhaengen (kein zusaetzliches
    # Leerzeichen), da der Vorschlag entweder ein Wortsuffix ist (Trie) oder sein
    # fuehrendes Leerzeichen bereits mitbringt (N-Gramm). Umfeld nur bei mitgeschicktem
    # Kontext (Datenschutz-Gate 'hier verbessern').
    basis = f"{anfrage.text_vor}{roh}" if anfrage.text_vor else uebernommen
    ngramm_speicher.lerne_text(basis, profil_id=profil)

    telemetrie.erfasse(
        engine=anfrage.uebernommen_engine or "",
        art="uebernahme",
        profil_id=profil,
        host=anfrage.seite.host,
        teil_uebernahme=anfrage.teil_uebernahme,
    )
    return LernAntwort(gelernt=True, hinweis="Woerter und N-Gramme aktualisiert.")
