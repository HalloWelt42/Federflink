"""Profil-Dienst: verbindet eingebaute Profile mit benutzerdefinierten (SQLite).

Eingebaute Profile sind schreibgeschützt; benutzerdefinierte lassen sich anlegen,
ändern und löschen. Host-Muster ordnen Seiten automatisch einem Profil zu.
"""

from __future__ import annotations

import fnmatch
import json
from datetime import UTC, datetime

from app.modelle.profil import Profil, ProfilAnlage
from app.modelle.system import ProfilInfo
from app.persistence.db import get_db
from app.profile.standard import EINGEBAUTE


def _jetzt() -> str:
    return datetime.now(UTC).isoformat()


def _db_profile() -> list[Profil]:
    with get_db().connect() as conn:
        zeilen = conn.execute(
            "SELECT id, name, sprache, beschreibung, stil_prompt, host_muster, aktiv FROM profile"
        ).fetchall()
    profile: list[Profil] = []
    for z in zeilen:
        try:
            muster = json.loads(z["host_muster"] or "[]")
        except json.JSONDecodeError:
            muster = []
        profile.append(
            Profil(
                id=z["id"],
                name=z["name"],
                sprache=z["sprache"],
                beschreibung=z["beschreibung"],
                stil_prompt=z["stil_prompt"],
                host_muster=list(muster),
                aktiv=bool(z["aktiv"]),
                eingebaut=False,
            )
        )
    return profile


def alle_profile() -> list[Profil]:
    """Eingebaute + benutzerdefinierte Profile (DB gewinnt bei gleicher Id)."""
    db = {p.id: p for p in _db_profile()}
    ergebnis = [db.get(p.id, p) for p in EINGEBAUTE]
    ergebnis += [p for p in db.values() if p.id not in {e.id for e in EINGEBAUTE}]
    return ergebnis


def hole_profil(profil_id: str) -> Profil | None:
    for p in alle_profile():
        if p.id == profil_id:
            return p
    return None


def stil_prompt(profil_id: str) -> str:
    p = hole_profil(profil_id)
    return p.stil_prompt if p else ""


def host_zu_profil(host: str) -> str | None:
    """Erstes Profil, dessen Host-Muster auf den Host passt."""
    host = (host or "").lower()
    if not host:
        return None
    for p in alle_profile():
        for muster in p.host_muster:
            if fnmatch.fnmatch(host, muster.lower()):
                return p.id
    return None


def profil_infos() -> list[ProfilInfo]:
    return [
        ProfilInfo(id=p.id, name=p.name, sprache=p.sprache, beschreibung=p.beschreibung)
        for p in alle_profile()
        if p.aktiv
    ]


def anlegen(anlage: ProfilAnlage) -> Profil:
    jetzt = _jetzt()
    with get_db().connect() as conn:
        conn.execute(
            """
            INSERT INTO profile (id, name, sprache, beschreibung, stil_prompt, host_muster, aktiv, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, 1, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                name=excluded.name, sprache=excluded.sprache, beschreibung=excluded.beschreibung,
                stil_prompt=excluded.stil_prompt, host_muster=excluded.host_muster, updated_at=excluded.updated_at
            """,
            (
                anlage.id,
                anlage.name,
                anlage.sprache,
                anlage.beschreibung,
                anlage.stil_prompt,
                json.dumps(anlage.host_muster),
                jetzt,
                jetzt,
            ),
        )
    profil = hole_profil(anlage.id)
    assert profil is not None
    return profil


def entfernen(profil_id: str) -> bool:
    """Löscht ein benutzerdefiniertes Profil. Eingebaute bleiben unberührt."""
    if any(e.id == profil_id for e in EINGEBAUTE):
        return False
    with get_db().connect() as conn:
        cur = conn.execute("DELETE FROM profile WHERE id = ?", (profil_id,))
        return cur.rowcount > 0
