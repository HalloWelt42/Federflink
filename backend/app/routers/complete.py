"""Endpunkt Textergänzung.

Zwei Betriebsarten je nach Accept-Header:
- application/json (Vorgabe): nur der schnelle Instant-Vorschlag (Trie/N-Gramm).
- text/event-stream: Progressive Enhancement per SSE - zuerst der Instant-Vorschlag
  (event: instant), dann - falls ein Sprachmodell aktiv/erreichbar ist - die
  gestreamte LLM-Fortsetzung (event: token) und der finale Vorschlag (event: upgrade),
  abgeschlossen mit event: done. Bricht der Client ab, endet die Generierung.
"""

from __future__ import annotations

import json
from collections.abc import AsyncIterator

from fastapi import APIRouter, Request
from fastapi.responses import StreamingResponse

from app import config, dispatcher
from app.ergaenzungs_engines import llm_engine
from app.fehler import LimitUeberschritten
from app.modelle.ergaenzung import ErgaenzungsAnfrage, ErgaenzungsAntwort

router = APIRouter(tags=["Ergänzung"])


def _frame(event: str, daten: dict[str, object]) -> str:
    return f"event: {event}\ndata: {json.dumps(daten, ensure_ascii=False)}\n\n"


def _streamende_engine(anfrage: ErgaenzungsAnfrage) -> object | None:
    for engine in dispatcher.waehle_engines(anfrage.engines, nur_instant=False):
        if getattr(engine, "streaming", False) and hasattr(engine, "stream"):
            return engine
    return None


async def _umfeld_kontext(anfrage: ErgaenzungsAnfrage) -> str | None:
    """Stilhinweis des Profils + ähnliche gelernte Passagen (Lernen Stufe 2)."""
    from app.lernen import kontext_speicher
    from app.profile import dienst

    profil = anfrage.profil_id or "standard"
    teile: list[str] = []
    stil = dienst.stil_prompt(profil)
    if stil:
        teile.append(stil)
    for passage in await kontext_speicher.aehnliche(anfrage.text_vor, profil_id=profil):
        teile.append(f"- {passage}")
    return "\n".join(teile) if teile else None


async def _sse(anfrage: ErgaenzungsAnfrage, request: Request) -> AsyncIterator[str]:
    instant = await dispatcher.ergaenze(anfrage)
    yield _frame(
        "instant",
        {
            "request_id": anfrage.request_id,
            "vorschlaege": [v.model_dump(mode="json") for v in instant.vorschlaege],
            "engine_status": instant.engine_status,
            "upgrade_aussteht": instant.upgrade_aussteht,
        },
    )

    engine = _streamende_engine(anfrage) if instant.upgrade_aussteht else None
    if engine is None:
        yield _frame("done", {"request_id": anfrage.request_id})
        return

    kontext = await _umfeld_kontext(anfrage)
    gesammelt = ""
    try:
        async for delta in engine.stream(anfrage, kontext):  # type: ignore[attr-defined]
            if await request.is_disconnected():
                return
            gesammelt += delta
            yield _frame("token", {"request_id": anfrage.request_id, "id": "llm", "delta": delta})
    except Exception:  # noqa: BLE001 - Modellfehler darf den Instant-Vorschlag nicht entwerten
        yield _frame("done", {"request_id": anfrage.request_id})
        return

    vorschlag = llm_engine.nachbereiten(anfrage, gesammelt)
    if vorschlag is not None:
        yield _frame(
            "upgrade",
            {"request_id": anfrage.request_id, "vorschlaege": [vorschlag.model_dump(mode="json")]},
        )
    yield _frame("done", {"request_id": anfrage.request_id})


@router.post("/complete")
async def complete(anfrage: ErgaenzungsAnfrage, request: Request):  # type: ignore[no-untyped-def]
    if len(anfrage.text_vor) > config.MAX_TEXT_ZEICHEN:
        raise LimitUeberschritten("Kontext zu lang.")
    if "text/event-stream" in request.headers.get("accept", ""):
        return StreamingResponse(_sse(anfrage, request), media_type="text/event-stream")
    antwort: ErgaenzungsAntwort = await dispatcher.ergaenze(anfrage)
    return antwort
