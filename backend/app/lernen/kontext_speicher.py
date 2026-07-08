"""Umfeld-Kontext (Lernen Stufe 2), eigenständig - ohne Fremd-App.

Akzeptierte Passagen werden über den lokalen Embedding-Endpunkt eingebettet und
als Vektor (float32-BLOB) in SQLite abgelegt. Bei einer Ergänzung werden die
ähnlichsten Passagen des Profils gesucht und dem Sprachmodell als Stilhinweis
mitgegeben. Ähnlichkeit per Kosinus in reinem Python (kein numpy nötig).
"""

from __future__ import annotations

import math
from array import array
from datetime import UTC, datetime

from app.persistence.db import get_db
from app.services import llm_client

# Obergrenze gespeicherter Passagen (älteste werden verworfen).
_MAX_PASSAGEN = 5000
_MIN_ZEICHEN = 12


def _jetzt() -> str:
    return datetime.now(UTC).isoformat()


def _pack(vektor: list[float]) -> bytes:
    return array("f", vektor).tobytes()


def _entpack(blob: bytes) -> list[float]:
    a = array("f")
    a.frombytes(blob)
    return list(a)


def _kosinus(a: list[float], b: list[float]) -> float:
    if len(a) != len(b):
        return 0.0
    punkt = sum(x * y for x, y in zip(a, b, strict=True))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return punkt / (na * nb)


async def merke_passage(text: str, *, profil_id: str = "standard", host: str = "") -> bool:
    """Bettet eine Passage ein und speichert sie. False, wenn kein Embedding möglich."""
    text = text.strip()
    if len(text) < _MIN_ZEICHEN:
        return False
    try:
        vektoren, modell, dim = await llm_client.embed([text])
    except llm_client.LlmFehler:
        return False
    if not vektoren:
        return False
    jetzt = _jetzt()
    with get_db().connect() as conn:
        conn.execute(
            """
            INSERT INTO kontext_passagen (profil_id, text, embedding, dim, modell, host, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (profil_id, text, _pack(vektoren[0]), dim, modell, host, jetzt),
        )
        # Älteste über der Obergrenze entfernen.
        conn.execute(
            """
            DELETE FROM kontext_passagen WHERE id IN (
                SELECT id FROM kontext_passagen ORDER BY id DESC LIMIT -1 OFFSET ?
            )
            """,
            (_MAX_PASSAGEN,),
        )
    return True


async def aehnliche(
    text: str, *, profil_id: str = "standard", top: int = 3, min_score: float = 0.55
) -> list[str]:
    """Ähnlichste gespeicherte Passagen (Text) zum Anfragetext."""
    text = text.strip()
    if len(text) < _MIN_ZEICHEN:
        return []
    try:
        vektoren, _modell, _dim = await llm_client.embed([text])
    except llm_client.LlmFehler:
        return []
    if not vektoren:
        return []
    frage = vektoren[0]

    with get_db().connect() as conn:
        zeilen = conn.execute(
            """
            SELECT text, embedding FROM kontext_passagen
            WHERE profil_id = ? OR profil_id = 'standard'
            ORDER BY id DESC LIMIT 3000
            """,
            (profil_id,),
        ).fetchall()

    bewertet: list[tuple[float, str]] = []
    for z in zeilen:
        score = _kosinus(frage, _entpack(z["embedding"]))
        if score >= min_score:
            bewertet.append((score, z["text"]))
    bewertet.sort(key=lambda kv: kv[0], reverse=True)
    return [t for _s, t in bewertet[:top]]


def anzahl() -> int:
    with get_db().connect() as conn:
        return int(conn.execute("SELECT COUNT(*) AS n FROM kontext_passagen").fetchone()["n"])
