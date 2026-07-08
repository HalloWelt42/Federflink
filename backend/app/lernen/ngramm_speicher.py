"""N-Gramm-Speicher (Lernen Stufe 1): sagt das naechste Wort voraus.

Lernt online aus uebernommenem Text. Der Praefix (die n-1 vorangehenden Woerter)
wird zum Vergleich klein geschrieben; das vorhergesagte Wort behaelt seine
gelernte Schreibung (wichtig fuer gross geschriebene Substantive).
"""

from __future__ import annotations

from datetime import UTC, datetime

from app.lernen import tokens
from app.persistence.db import get_db

# Gelernte N-Gramm-Ordnungen: Bigramm (n=2) und Trigramm (n=3).
_ORDNUNGEN = (2, 3)
_MAX_WORTE_JE_LERNVORGANG = 400


def _jetzt() -> str:
    return datetime.now(UTC).isoformat()


def lerne_text(text: str, *, profil_id: str = "standard") -> int:
    """Zaehlt alle Bi-/Trigramme des Textes hoch. Liefert die Zahl gelernter N-Gramme."""
    ws = tokens.woerter(text)[:_MAX_WORTE_JE_LERNVORGANG]
    if len(ws) < 2:
        return 0
    jetzt = _jetzt()
    gelernt = 0
    with get_db().connect() as conn:
        for n in _ORDNUNGEN:
            for i in range(len(ws) - n + 1):
                praefix = " ".join(w.lower() for w in ws[i : i + n - 1])
                wort = ws[i + n - 1]
                conn.execute(
                    """
                    INSERT INTO ngramme (profil_id, n, praefix, wort, haeufigkeit, updated_at)
                    VALUES (?, ?, ?, ?, 1, ?)
                    ON CONFLICT(profil_id, n, praefix, wort)
                    DO UPDATE SET haeufigkeit = haeufigkeit + 1, updated_at = excluded.updated_at
                    """,
                    (profil_id, n, praefix, wort, jetzt),
                )
                gelernt += 1
    return gelernt


def _abfrage(praefix_woerter: list[str], n: int, profil_id: str, top: int) -> list[tuple[str, int]]:
    if len(praefix_woerter) < n - 1:
        return []
    praefix = " ".join(w.lower() for w in praefix_woerter[-(n - 1) :])
    with get_db().connect() as conn:
        zeilen = conn.execute(
            """
            SELECT wort, SUM(haeufigkeit) AS h FROM ngramme
            WHERE n = ? AND praefix = ? AND (profil_id = ? OR profil_id = 'standard')
            GROUP BY wort ORDER BY h DESC LIMIT ?
            """,
            (n, praefix, profil_id, top),
        ).fetchall()
    return [(z["wort"], int(z["h"])) for z in zeilen]


def vorhersage_naechstes(
    vorher_woerter: list[str], *, profil_id: str = "standard", top: int = 5
) -> list[tuple[str, int]]:
    """Naechstes Wort: bevorzugt Trigramm, faellt auf Bigramm zurueck."""
    ergebnis: dict[str, int] = {}
    for n in (3, 2):
        for wort, h in _abfrage(vorher_woerter, n, profil_id, top):
            # Hoehere Ordnung zaehlt staerker (einfache Gewichtung).
            ergebnis[wort] = ergebnis.get(wort, 0) + h * (2 if n == 3 else 1)
    return sorted(ergebnis.items(), key=lambda kv: kv[1], reverse=True)[:top]


def vorhersage_phrase(
    vorher_woerter: list[str], *, profil_id: str = "standard", max_woerter: int = 3, min_count: int = 2
) -> list[str]:
    """Greedy-Fortsetzung ueber mehrere Woerter, solange sie hinreichend belegt ist."""
    phrase: list[str] = []
    kontext = list(vorher_woerter)
    for _ in range(max_woerter):
        kandidaten = vorhersage_naechstes(kontext, profil_id=profil_id, top=1)
        if not kandidaten or kandidaten[0][1] < min_count:
            break
        wort = kandidaten[0][0]
        phrase.append(wort)
        kontext.append(wort)
    return phrase


def anzahl() -> int:
    with get_db().connect() as conn:
        return int(conn.execute("SELECT COUNT(*) AS n FROM ngramme").fetchone()["n"])
