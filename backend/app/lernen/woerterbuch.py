"""Persoenliches Woerterbuch (Lernen Stufe 1).

Woerter, die der Nutzer schreibt, uebernimmt oder manuell hinzufuegt, werden hier
gezaehlt. Sie heben Rechtschreib-Warnungen fuer Eigennamen/Fachbegriffe auf und
fliessen spaeter in die Wortergaenzung (Trie) ein.
"""

from __future__ import annotations

from datetime import UTC, datetime

from app.persistence.db import get_db


def _jetzt() -> str:
    return datetime.now(UTC).isoformat()


def bekannte_woerter(profil_id: str = "standard") -> set[str]:
    """Liefert die klein geschriebenen bekannten Woerter eines Profils.

    Das Standard-Profil gilt zusaetzlich als Grundwortschatz fuer alle Profile.
    """
    with get_db().connect() as conn:
        zeilen = conn.execute(
            "SELECT wort FROM woerter WHERE profil_id = ? OR profil_id = 'standard'",
            (profil_id,),
        ).fetchall()
    return {z["wort"].lower() for z in zeilen}


def hinzufuegen(wort: str, *, profil_id: str = "standard", quelle: str = "manuell") -> None:
    """Fuegt ein Wort hinzu oder erhoeht seine Haeufigkeit (idempotent)."""
    wort = wort.strip()
    if not wort:
        return
    jetzt = _jetzt()
    with get_db().connect() as conn:
        conn.execute(
            """
            INSERT INTO woerter (wort, profil_id, haeufigkeit, quelle, created_at, updated_at)
            VALUES (?, ?, 1, ?, ?, ?)
            ON CONFLICT(wort, profil_id)
            DO UPDATE SET haeufigkeit = haeufigkeit + 1, updated_at = excluded.updated_at
            """,
            (wort, profil_id, quelle, jetzt, jetzt),
        )


def liste(profil_id: str | None = None, *, limit: int = 500) -> list[dict[str, object]]:
    """Woerter fuer die Verwaltung im UI (haeufigste zuerst)."""
    with get_db().connect() as conn:
        if profil_id:
            zeilen = conn.execute(
                "SELECT wort, profil_id, haeufigkeit, quelle FROM woerter "
                "WHERE profil_id = ? ORDER BY haeufigkeit DESC, wort ASC LIMIT ?",
                (profil_id, limit),
            ).fetchall()
        else:
            zeilen = conn.execute(
                "SELECT wort, profil_id, haeufigkeit, quelle FROM woerter "
                "ORDER BY haeufigkeit DESC, wort ASC LIMIT ?",
                (limit,),
            ).fetchall()
    return [dict(z) for z in zeilen]


def entfernen(wort: str, profil_id: str = "standard") -> bool:
    with get_db().connect() as conn:
        cur = conn.execute(
            "DELETE FROM woerter WHERE wort = ? AND profil_id = ?", (wort, profil_id)
        )
        return cur.rowcount > 0


def anzahl() -> int:
    with get_db().connect() as conn:
        return int(conn.execute("SELECT COUNT(*) AS n FROM woerter").fetchone()["n"])
