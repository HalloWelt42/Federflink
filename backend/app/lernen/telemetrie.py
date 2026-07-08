"""Telemetrie: Annahme/Ablehnung je Engine (fuer Admin-Transparenz im Status)."""

from __future__ import annotations

from datetime import UTC, datetime

from app.persistence.db import get_db


def erfasse(
    *, engine: str, art: str, profil_id: str = "standard", host: str = "", teil_uebernahme: bool = False
) -> None:
    with get_db().connect() as conn:
        conn.execute(
            """
            INSERT INTO lern_ereignisse (engine, art, profil_id, host, teil_uebernahme, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (engine, art, profil_id, host, 1 if teil_uebernahme else 0, datetime.now(UTC).isoformat()),
        )


def zusammenfassung() -> list[dict[str, object]]:
    """Annahmen je Engine (haeufigste zuerst) - fuer die Statusansicht."""
    with get_db().connect() as conn:
        zeilen = conn.execute(
            """
            SELECT engine,
                   SUM(CASE WHEN art = 'uebernahme' THEN 1 ELSE 0 END) AS uebernahmen,
                   SUM(CASE WHEN art = 'ablehnung' THEN 1 ELSE 0 END) AS ablehnungen
            FROM lern_ereignisse GROUP BY engine ORDER BY uebernahmen DESC
            """
        ).fetchall()
    return [dict(z) for z in zeilen]
