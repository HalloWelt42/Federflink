"""Endpunkt Lernsignal: verarbeitet übernommene Vorschläge (Lernen Stufe 1).

- Unbekannte Wörter wandern ins persönliche Wörterbuch (Hunspell kennt sie dann).
- N-Gramme werden aus dem Umfeld (Text vor dem Cursor + Übernahme) gelernt,
  aber nur wenn der Client den Kontext mitschickt (Datenschutz-Gate 'hier verbessern').
- Jede Übernahme/Ablehnung wird für die Statusansicht gezählt.
"""

from __future__ import annotations

from app.lernen import kontext_speicher, ngramm_speicher, telemetrie, tokens, woerterbuch
from app.modelle.ergaenzung import LernAnfrage, LernAntwort
from app.pruef_engines import hunspell_engine
from fastapi import APIRouter

router = APIRouter(tags=["Lernen"])


@router.post("/learn")
async def learn(anfrage: LernAnfrage) -> LernAntwort:
    profil = anfrage.profil_id or "standard"
    roh = anfrage.uebernommen_text  # Rohform: Vorschlag kann Suffix oder führendes Leerzeichen tragen
    uebernommen = roh.strip()

    if not uebernommen:
        telemetrie.erfasse(
            engine=anfrage.uebernommen_engine or "",
            art="ablehnung",
            profil_id=profil,
            host=anfrage.seite.host,
        )
        return LernAntwort(gelernt=False, hinweis="Nichts übernommen.")

    # Unbekannte Wörter ins persönliche Wörterbuch (nicht die Allerweltswörter).
    for wort in tokens.woerter(uebernommen):
        if len(wort) < 3:
            continue
        if hunspell_engine.kennt_wort(wort) is False:
            woerterbuch.hinzufuegen(wort, profil_id=profil, quelle="gelernt")

    # N-Gramme lernen. WICHTIG: direkt aneinanderhängen (kein zusätzliches
    # Leerzeichen), da der Vorschlag entweder ein Wortsuffix ist (Trie) oder sein
    # führendes Leerzeichen bereits mitbringt (N-Gramm). Umfeld nur bei mitgeschicktem
    # Kontext (Datenschutz-Gate 'hier verbessern').
    basis = f"{anfrage.text_vor}{roh}" if anfrage.text_vor else uebernommen
    ngramm_speicher.lerne_text(basis, profil_id=profil)

    # Umfeld-Kontext (Stufe 2) nur bei längeren, mehrwortigen Übernahmen mit
    # mitgeschicktem Kontext lernen - so bleiben die Embedding-Aufrufe sparsam.
    if anfrage.text_vor and " " in uebernommen:
        passage = f"{anfrage.text_vor[-200:]}{roh}".strip()
        await kontext_speicher.merke_passage(passage, profil_id=profil, host=anfrage.seite.host)

    telemetrie.erfasse(
        engine=anfrage.uebernommen_engine or "",
        art="uebernahme",
        profil_id=profil,
        host=anfrage.seite.host,
        teil_uebernahme=anfrage.teil_uebernahme,
    )
    return LernAntwort(gelernt=True, hinweis="Wörter und N-Gramme aktualisiert.")
