"""Typisierte Registries mit Dekorator-Registrierung und Modul-Discovery.

Neue Engines entstehen, indem eine Datei ins passende Paket gelegt wird
(app.pruef_engines bzw. app.ergaenzungs_engines) - der Import beim App-Start
loest den Dekorator aus, der Capabilities-Endpunkt macht sie dem Frontend und
der Browser-Erweiterung ohne weitere Aenderung bekannt.
"""

from __future__ import annotations

import importlib
import pkgutil

from app import config
from app.fehler import ModulUnbekannt
from app.modelle.ergaenzung import ErgaenzungsModus
from app.modelle.system import (
    CapabilitiesAntwort,
    EngineInfo,
    Grenzen,
    LlmStatus,
)
from app.schnittstellen.ergaenzungs_engine import ErgaenzungsEngine
from app.schnittstellen.pruef_engine import PruefEngine


class RegistrierungsFehler(RuntimeError):
    pass


class Registry[T]:
    def __init__(self, name: str) -> None:
        self._name = name
        self._eintraege: dict[str, T] = {}

    def registriere(self, schluessel: str, eintrag: T) -> None:
        if schluessel in self._eintraege:
            raise RegistrierungsFehler(f"{self._name}: '{schluessel}' ist doppelt registriert")
        self._eintraege[schluessel] = eintrag

    def hole(self, schluessel: str) -> T:
        eintrag = self._eintraege.get(schluessel)
        if eintrag is None:
            bekannte = ", ".join(sorted(self._eintraege)) or "-"
            raise ModulUnbekannt(f"{self._name} '{schluessel}' ist unbekannt (bekannt: {bekannte})")
        return eintrag

    def alle(self) -> tuple[T, ...]:
        return tuple(self._eintraege.values())

    def leeren(self) -> None:
        self._eintraege.clear()


pruef_engines: Registry[PruefEngine] = Registry("PruefEngine")
ergaenzungs_engines: Registry[ErgaenzungsEngine] = Registry("ErgaenzungsEngine")


def pruef_engine[E: PruefEngine](cls: type[E]) -> type[E]:
    """Klassen-Dekorator: registriert eine Instanz der Pruef-Engine unter ihrer engine_id."""
    pruef_engines.registriere(cls.engine_id, cls())
    return cls


def ergaenzungs_engine[E: ErgaenzungsEngine](cls: type[E]) -> type[E]:
    """Klassen-Dekorator: registriert eine Instanz der Ergaenzungs-Engine unter ihrer engine_id."""
    ergaenzungs_engines.registriere(cls.engine_id, cls())
    return cls


_MODUL_PAKETE = ("app.pruef_engines", "app.ergaenzungs_engines")
_entdeckt = False


def entdecke_module() -> None:
    """Importiert alle Untermodule der Engine-Pakete; Importe loesen die Dekoratoren aus."""
    global _entdeckt
    if _entdeckt:
        return
    for paketname in _MODUL_PAKETE:
        paket = importlib.import_module(paketname)
        for modul_info in pkgutil.iter_modules(paket.__path__):
            importlib.import_module(f"{paketname}.{modul_info.name}")
    _entdeckt = True


def _pruef_engine_infos() -> list[EngineInfo]:
    infos: list[EngineInfo] = []
    for eintrag in sorted(pruef_engines.alle(), key=lambda e: e.engine_id):
        infos.append(
            EngineInfo(
                id=eintrag.engine_id,
                name=eintrag.name,
                aktiv=_sicher_verfuegbar(eintrag),
                standard_an=eintrag.standard_an,
                streaming=False,
            )
        )
    return infos


def _ergaenzungs_engine_infos() -> list[EngineInfo]:
    infos: list[EngineInfo] = []
    for eintrag in sorted(ergaenzungs_engines.alle(), key=lambda e: e.engine_id):
        infos.append(
            EngineInfo(
                id=eintrag.engine_id,
                name=eintrag.name,
                aktiv=_sicher_verfuegbar(eintrag),
                standard_an=eintrag.standard_an,
                streaming=eintrag.streaming,
            )
        )
    return infos


def _sicher_verfuegbar(eintrag: object) -> bool:
    """ist_verfuegbar() darf nie den Capabilities-Endpunkt sprengen."""
    pruefer = getattr(eintrag, "ist_verfuegbar", None)
    if not callable(pruefer):
        return True
    try:
        return bool(pruefer())
    except Exception:  # noqa: BLE001 - defensiv, Diagnose-Endpunkt
        return False


async def capabilities() -> CapabilitiesAntwort:
    # LLM-Status ist kurz zwischengespeichert (siehe llm_client), damit dieser
    # Endpunkt schnell bleibt, auch wenn kein Modell-Server laeuft.
    from app.profile.dienst import profil_infos
    from app.services import llm_client

    zustand = await llm_client.status()
    llm = LlmStatus(
        erreichbar=bool(zustand["erreichbar"]),
        url=str(zustand["url"]),
        modelle=list(zustand["modelle"]),  # type: ignore[arg-type]
    )
    return CapabilitiesAntwort(
        version=config.APP_VERSION,
        pruef_engines=_pruef_engine_infos(),
        ergaenzungs_engines=_ergaenzungs_engine_infos(),
        modi=[m.value for m in ErgaenzungsModus],
        profile=profil_infos(),
        grenzen=Grenzen(
            budget_vor=config.BUDGET_VOR_ZEICHEN,
            budget_nach=config.BUDGET_NACH_ZEICHEN,
            debounce_ms=config.DEBOUNCE_MS,
            min_zeichen=config.MIN_ZEICHEN,
            max_vorschlaege=config.MAX_VORSCHLAEGE,
            max_text_zeichen=config.MAX_TEXT_ZEICHEN,
        ),
        funktionen={"sse": True, "lernen": True, "teil_uebernahme": True},
        llm=llm,
    )
