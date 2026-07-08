"""Anbindung an einen lokalen, OpenAI-kompatiblen Server (LM Studio / Ollama / llama.cpp).

Kernpunkte:
- JIT-sichere Modellwahl: bevorzugt das tatsächlich GELADENE Modell (native
  /api/v0/models von LM Studio), damit nicht versehentlich ein anderes per
  JIT-Loading geladen wird. Fällt diese Auskunft weg (z. B. Ollama), wird das
  konfigurierte bzw. erste gemeldete Modell genutzt.
- SSRF-Schutz: die Basis-URL muss auf localhost/privates Netz zeigen.
- Nicht-streamend (chat) für Korrektur; Streaming ergänzt Phase 3.
"""

from __future__ import annotations

import ipaddress
import json
import time
from collections.abc import AsyncIterator
from urllib.parse import urlparse

import httpx

from app import config


class LlmFehler(RuntimeError):
    """Kommunikationsfehler mit dem Sprachmodell-Server."""


def basis_url() -> str:
    return config.LLM_URL.rstrip("/")


def pruefe_url(url: str) -> None:
    """Erlaubt nur http/https auf loopback oder private Adressen (SSRF-Schutz)."""
    zerlegt = urlparse(url)
    if zerlegt.scheme not in ("http", "https"):
        raise LlmFehler(f"Ungültiges Schema: {zerlegt.scheme}")
    host = zerlegt.hostname or ""
    if host in ("localhost", "127.0.0.1", "::1"):
        return
    try:
        adresse = ipaddress.ip_address(host)
    except ValueError:
        # Hostnamen (nicht-IP) nur zulassen, wenn sie offensichtlich lokal sind.
        if host.endswith(".local") or host == "host.docker.internal":
            return
        raise LlmFehler(f"Nur lokale Ziele erlaubt, nicht: {host}") from None
    if not (adresse.is_loopback or adresse.is_private):
        raise LlmFehler(f"Nur lokale/private Adressen erlaubt, nicht: {host}")


async def list_models(url: str | None = None, timeout: float = 3.0) -> list[str]:
    base = (url or basis_url()).rstrip("/")
    pruefe_url(base)
    async with httpx.AsyncClient(timeout=timeout) as client:
        resp = await client.get(f"{base}/v1/models")
        resp.raise_for_status()
        data = resp.json()
    return [m["id"] for m in data.get("data", []) if "id" in m]


async def geladene_chat_modelle(url: str | None = None, timeout: float = 2.0) -> list[str]:
    """IDs der aktuell GELADENEN Chat-Modelle laut nativer /api/v0/models (LM Studio)."""
    base = (url or basis_url()).rstrip("/")
    try:
        pruefe_url(base)
        async with httpx.AsyncClient(timeout=timeout) as client:
            resp = await client.get(f"{base}/api/v0/models")
            if resp.status_code != 200:
                return []
            rows = resp.json().get("data", [])
    except Exception:  # noqa: BLE001 - Server ohne diese Route (z. B. Ollama)
        return []
    return [
        m.get("id", "")
        for m in rows
        if m.get("state") == "loaded" and m.get("type") in ("llm", "vlm") and m.get("id")
    ]


# Modell-Namensteile, die auf ein NICHT für Chat/Korrektur geeignetes Modell deuten.
_AUSSCHLUSS = ("embed", "rerank", "image", "-vl", "vl-", "vision", "ocr", "whisper", "tts", "edit")


async def resolve_chat_modell(url: str | None = None, preferred: str | None = None) -> str:
    """Bestimmt ein Chat-Modell.

    Reihenfolge: ausdrücklich übergeben -> aktuell GELADENES Modell (kein JIT) ->
    konfigurierter Default -> bestes gemeldetes Modell (löst JIT aus). Bei der
    letzten Stufe werden Embedding-/Bild-/Vision-Modelle übersprungen und
    Instruct-Modelle bevorzugt, damit nicht versehentlich ein ungeeignetes (z. B.
    Reasoning-/Bild-)Modell geladen wird.
    """
    base = (url or basis_url()).rstrip("/")
    if preferred and preferred.strip():
        return preferred.strip()
    geladen = await geladene_chat_modelle(base)
    if geladen:
        return geladen[0]
    default = (config.DEFAULT_CHAT_MODELL or "").strip()
    if default:
        return default
    modelle = await list_models(base)
    if not modelle:
        raise LlmFehler("Kein Sprachmodell gemeldet.")
    kandidaten = [m for m in modelle if not any(teil in m.lower() for teil in _AUSSCHLUSS)]
    bevorzugt = [m for m in kandidaten if "instruct" in m.lower()]
    return (bevorzugt or kandidaten or modelle)[0]


async def chat(
    messages: list[dict[str, str]],
    *,
    model: str | None = None,
    url: str | None = None,
    temperature: float = 0.0,
    max_tokens: int = -1,
    timeout: float | None = None,
) -> str:
    """Ruft eine Chat-Completion (nicht streamend) auf und liefert den Antworttext."""
    base = (url or basis_url()).rstrip("/")
    pruefe_url(base)
    verwendetes = await resolve_chat_modell(base, model)
    payload: dict[str, object] = {
        "model": verwendetes,
        "messages": messages,
        "temperature": temperature,
        "stream": False,
    }
    if max_tokens and max_tokens > 0:
        payload["max_tokens"] = max_tokens
    try:
        async with httpx.AsyncClient(timeout=timeout or config.LLM_TIMEOUT_S) as client:
            resp = await client.post(f"{base}/v1/chat/completions", json=payload)
            if resp.status_code != 200:
                detail = ""
                try:
                    detail = resp.json().get("error", "") or resp.text
                except Exception:  # noqa: BLE001
                    detail = resp.text
                raise LlmFehler(f"Chat fehlgeschlagen (HTTP {resp.status_code}): {str(detail)[:300]}")
            data = resp.json()
    except httpx.HTTPError as exc:
        grund = str(exc) or type(exc).__name__
        raise LlmFehler(f"Chat fehlgeschlagen: {grund}") from exc
    try:
        return (data["choices"][0]["message"]["content"] or "").strip()
    except (KeyError, IndexError):
        return ""


async def resolve_embedding_modell(url: str | None = None, preferred: str | None = None) -> str:
    """Bestimmt ein Embedding-Modell (Heuristik: 'embed' im Namen)."""
    base = (url or basis_url()).rstrip("/")
    kandidat = (preferred or config.DEFAULT_EMBEDDING_MODELL or "").strip()
    if kandidat:
        return kandidat
    modelle = await list_models(base)
    if not modelle:
        raise LlmFehler("Kein Embedding-Modell gemeldet.")
    for m in modelle:
        if "embed" in m.lower():
            return m
    return modelle[0]


async def embed(
    texte: list[str], *, model: str | None = None, url: str | None = None, timeout: float | None = None
) -> tuple[list[list[float]], str, int]:
    """Bettet Texte ein. Liefert (Vektoren, verwendetes Modell, Dimension)."""
    if not texte:
        return [], (model or ""), 0
    base = (url or basis_url()).rstrip("/")
    pruefe_url(base)
    verwendetes = await resolve_embedding_modell(base, model)
    try:
        async with httpx.AsyncClient(timeout=timeout or config.LLM_TIMEOUT_S) as client:
            resp = await client.post(
                f"{base}/v1/embeddings", json={"model": verwendetes, "input": texte}
            )
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPError as exc:
        raise LlmFehler(f"Embedding fehlgeschlagen: {exc}") from exc
    eintraege = sorted(data.get("data", []), key=lambda d: d.get("index", 0))
    vektoren = [e["embedding"] for e in eintraege]
    if not vektoren:
        raise LlmFehler("Keine Embeddings erhalten.")
    return vektoren, verwendetes, len(vektoren[0])


async def chat_stream(
    messages: list[dict[str, str]],
    *,
    model: str | None = None,
    url: str | None = None,
    temperature: float = 0.2,
    max_tokens: int = -1,
    timeout: float | None = None,
) -> AsyncIterator[str]:
    """Streamt eine Chat-Completion und liefert die Text-Deltas nacheinander."""
    base = (url or basis_url()).rstrip("/")
    pruefe_url(base)
    verwendetes = await resolve_chat_modell(base, model)
    payload: dict[str, object] = {
        "model": verwendetes,
        "messages": messages,
        "temperature": temperature,
        "stream": True,
    }
    if max_tokens and max_tokens > 0:
        payload["max_tokens"] = max_tokens
    async with httpx.AsyncClient(timeout=timeout or config.LLM_TIMEOUT_S) as client:
        async with client.stream("POST", f"{base}/v1/chat/completions", json=payload) as resp:
            if resp.status_code != 200:
                await resp.aread()
                raise LlmFehler(f"Streaming fehlgeschlagen (HTTP {resp.status_code}).")
            async for zeile in resp.aiter_lines():
                if not zeile or not zeile.startswith("data:"):
                    continue
                rest = zeile[5:].strip()
                if rest == "[DONE]":
                    break
                try:
                    obj = json.loads(rest)
                    delta = obj["choices"][0]["delta"].get("content")
                except (json.JSONDecodeError, KeyError, IndexError):
                    continue
                if delta:
                    yield delta


# ---- Zustands-Auskunft (kurz zwischengespeichert, damit /capabilities schnell bleibt) ----
_status_cache: tuple[float, dict[str, object]] | None = None
_STATUS_TTL = 5.0


def zuletzt_erreichbar() -> bool:
    """Letzter bekannter Erreichbarkeitszustand ohne Netzaufruf (für ist_verfuegbar).

    Ohne bisherigen Status optimistisch True - ein echter Ausfall wird beim Aufruf
    ohnehin sauber abgefangen.
    """
    if _status_cache is None:
        return True
    return bool(_status_cache[1].get("erreichbar", False))


async def status(url: str | None = None) -> dict[str, object]:
    """Erreichbarkeit + gemeldete Modelle, mit kurzem Cache."""
    global _status_cache
    base = (url or basis_url()).rstrip("/")
    jetzt = time.monotonic()
    if _status_cache is not None and jetzt - _status_cache[0] < _STATUS_TTL:
        return _status_cache[1]
    try:
        modelle = await list_models(base, timeout=2.0)
        ergebnis: dict[str, object] = {"erreichbar": True, "url": base, "modelle": modelle}
    except Exception:  # noqa: BLE001 - Diagnose, alles abfangen
        ergebnis = {"erreichbar": False, "url": base, "modelle": []}
    _status_cache = (jetzt, ergebnis)
    return ergebnis
