/**
 * TypeScript-Spiegel der Backend-Modelle (siehe backend/app/modelle).
 * Bei Aenderungen am Backend hier nachziehen.
 */

export interface FehlerDetail {
  code: string
  meldung: string
  details?: Record<string, unknown>
  request_id?: string
}

export interface FehlerAntwort {
  fehler: FehlerDetail
}

export interface HealthAntwort {
  status: string
  name: string
  version: string
}

export interface EngineInfo {
  id: string
  name: string
  aktiv: boolean
  standard_an: boolean
  streaming: boolean
}

export interface ProfilInfo {
  id: string
  name: string
  sprache: string
  beschreibung: string
}

export interface Grenzen {
  budget_vor: number
  budget_nach: number
  debounce_ms: number
  min_zeichen: number
  max_vorschlaege: number
  max_text_zeichen: number
}

export interface LlmStatus {
  erreichbar: boolean
  url: string
  modelle: string[]
}

export interface CapabilitiesAntwort {
  version: string
  name: string
  pruef_engines: EngineInfo[]
  ergaenzungs_engines: EngineInfo[]
  modi: string[]
  profile: ProfilInfo[]
  grenzen: Grenzen
  funktionen: Record<string, boolean>
  llm: LlmStatus | null
}
