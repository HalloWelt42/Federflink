/**
 * TypeScript-Spiegel der Backend-Modelle (siehe backend/app/modelle).
 * Bei Änderungen am Backend hier nachziehen.
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

export type BefundArt = 'rechtschreibung' | 'grammatik' | 'zeichensetzung' | 'stil' | 'tippfehler'

export interface Befund {
  offset: number
  laenge: number
  art: BefundArt
  meldung: string
  regel_id: string | null
  vorschlaege: string[]
  engine: string
}

export interface PruefAntwort {
  befunde: Befund[]
  engines: string[]
  dauer_ms: number
}

export interface KorrekturAntwort {
  original: string
  korrigiert: string
  engine: string
  veraendert: boolean
}

export interface SatzAntwort {
  satz: string
  vorschlaege: string[]
}

export interface WortEintrag {
  wort: string
  profil_id: string
  haeufigkeit: number
  quelle: string
}

export interface WoerterbuchListe {
  woerter: WortEintrag[]
  anzahl: number
}

export type ErgaenzungsModus = 'wort' | 'phrase' | 'satz'

export interface Vorschlag {
  id: string
  text: string
  engine: string
  score: number
  art: ErgaenzungsModus
  ersetze_vor: number
  anzeige_text: string | null
  final: boolean
}

export interface ErgaenzungsAntwort {
  request_id: string
  erzeugt_ms: number
  vorschlaege: Vorschlag[]
  upgrade_aussteht: boolean
  engine_status: Record<string, string>
}

export interface EngineAnnahme {
  engine: string
  uebernahmen: number
  ablehnungen: number
}

export interface LernStatus {
  woerter: number
  ngramme: number
  kontext: number
  annahmen: EngineAnnahme[]
}

export interface Profil {
  id: string
  name: string
  sprache: string
  beschreibung: string
  stil_prompt: string
  host_muster: string[]
  aktiv: boolean
  eingebaut: boolean
}
