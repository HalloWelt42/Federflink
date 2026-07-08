/**
 * Zentraler HTTP-Helfer. Kapselt JSON-Parsing und Fehlerbehandlung, damit die
 * fachlichen API-Funktionen schlank bleiben. Das Backend liefert Fehler als
 * FehlerAntwort ({ fehler: { code, meldung, ... } }). Pfade sind relativ (/api/...)
 * und laufen ueber den Vite-Proxy - keine fest verdrahtete Basis-URL.
 */

import type { FehlerAntwort, FehlerDetail } from './typen'

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly code: string,
    public readonly meldung: string,
    public readonly detail: FehlerDetail | null = null,
  ) {
    super(`Backend-Fehler ${status} (${code}): ${meldung}`)
    this.name = 'ApiError'
  }
}

async function fehlerAusAntwort(antwort: Response): Promise<ApiError> {
  const body = await antwort.text()
  try {
    const daten = JSON.parse(body) as Partial<FehlerAntwort>
    const detail = daten.fehler
    if (detail && typeof detail.code === 'string' && typeof detail.meldung === 'string') {
      return new ApiError(antwort.status, detail.code, detail.meldung, detail as FehlerDetail)
    }
  } catch {
    // Body war kein JSON - Fallback unten.
  }
  return new ApiError(antwort.status, 'unbekannt', body || antwort.statusText)
}

export async function requestJson<T>(pfad: string, init: RequestInit = {}): Promise<T> {
  const antwort = await fetch(pfad, {
    headers: { 'Content-Type': 'application/json', ...(init.headers ?? {}) },
    ...init,
  })
  if (!antwort.ok) {
    throw await fehlerAusAntwort(antwort)
  }
  return (await antwort.json()) as T
}
