"""Fehlertaxonomie und FastAPI-Exception-Handler.

Jede fachliche Ausnahme trägt einen stabilen Maschinen-Code und einen HTTP-Status;
die Handler formen alles in das einheitliche FehlerAntwort-Modell um.
"""

from __future__ import annotations

from typing import Any
from uuid import UUID, uuid4

from fastapi import FastAPI, Request
from fastapi.encoders import jsonable_encoder
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.modelle.gemeinsam import FehlerAntwort, FehlerDetail, JsonWert


class FederflinkFehler(Exception):
    """Basis aller fachlichen Fehler."""

    code: str = "intern"
    status: int = 500

    def __init__(self, meldung: str, *, details: dict[str, JsonWert] | None = None) -> None:
        super().__init__(meldung)
        self.meldung = meldung
        self.details: dict[str, JsonWert] = details or {}


class ModulUnbekannt(FederflinkFehler):
    code = "modul_unbekannt"
    status = 404


class LimitUeberschritten(FederflinkFehler):
    code = "limit_ueberschritten"
    status = 413


class EngineNichtVerfuegbar(FederflinkFehler):
    """Eine angeforderte Engine ist nicht aktiv (z. B. LanguageTool ohne Java)."""

    code = "engine_nicht_verfuegbar"
    status = 409


class LlmNichtErreichbar(FederflinkFehler):
    """Das lokale Sprachmodell antwortet nicht (Verbindungs- oder Netzwerkfehler)."""

    code = "llm_nicht_erreichbar"
    status = 502


class LlmAntwortUngueltig(FederflinkFehler):
    """Die Antwort des Sprachmodells ließ sich nicht auswerten."""

    code = "llm_antwort_ungueltig"
    status = 502


def _request_id(request: Request) -> UUID:
    kennung = getattr(request.state, "request_id", None)
    return kennung if isinstance(kennung, UUID) else uuid4()


def _antwort(status: int, detail: FehlerDetail) -> JSONResponse:
    return JSONResponse(
        status_code=status,
        content=FehlerAntwort(fehler=detail).model_dump(mode="json"),
        headers={"X-Request-Id": str(detail.request_id)},
    )


def registriere_fehler_handler(app: FastAPI) -> None:
    @app.exception_handler(FederflinkFehler)
    async def fachlicher_fehler(request: Request, exc: FederflinkFehler) -> JSONResponse:
        detail = FehlerDetail(
            code=exc.code,
            meldung=exc.meldung,
            details=exc.details,
            request_id=_request_id(request),
        )
        return _antwort(exc.status, detail)

    @app.exception_handler(RequestValidationError)
    async def eingabe_fehler(request: Request, exc: RequestValidationError) -> JSONResponse:
        felder = jsonable_encoder(exc.errors(), custom_encoder={Exception: str})
        einzelheiten: dict[str, Any] = {"felder": felder}
        detail = FehlerDetail(
            code="eingabe_ungueltig",
            meldung="Die Anfrage ist ungültig - Details unter 'felder'.",
            details=einzelheiten,
            request_id=_request_id(request),
        )
        return _antwort(422, detail)

    @app.exception_handler(Exception)
    async def unerwarteter_fehler(request: Request, exc: Exception) -> JSONResponse:
        detail = FehlerDetail(
            code="intern",
            meldung="Unerwarteter Fehler im Backend.",
            details={"art": type(exc).__name__},
            request_id=_request_id(request),
        )
        return _antwort(500, detail)
