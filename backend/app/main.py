"""App-Fabrik: Middleware, Fehler-Handler, Datenbank, Modul-Discovery, Router."""

from __future__ import annotations

from uuid import uuid4

from fastapi import FastAPI, Request, Response
from fastapi.middleware.cors import CORSMiddleware

from app import config, registry
from app.fehler import registriere_fehler_handler
from app.persistence.db import get_db
from app.routers import correct, spellcheck, system, woerterbuch


def create_app() -> FastAPI:
    app = FastAPI(
        title="Federflink",
        version=config.APP_VERSION,
        docs_url="/docs",
        openapi_url="/openapi.json",
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=list(config.FRONTEND_URSPRUENGE),
        allow_origin_regex=config.EXTENSION_URSPRUNG_REGEX,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def request_id(request: Request, call_next) -> Response:  # type: ignore[no-untyped-def]
        request.state.request_id = uuid4()
        antwort: Response = await call_next(request)
        antwort.headers.setdefault("X-Request-Id", str(request.state.request_id))
        return antwort

    registriere_fehler_handler(app)
    get_db().init_schema()
    registry.entdecke_module()

    app.include_router(system.router, prefix="/api")
    app.include_router(spellcheck.router, prefix="/api")
    app.include_router(correct.router, prefix="/api")
    app.include_router(woerterbuch.router, prefix="/api")
    return app


app = create_app()
