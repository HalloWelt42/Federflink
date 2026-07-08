/** API: Textergaenzung und Lernsignal. */

import { requestJson } from './http'
import type { ErgaenzungsAntwort, ErgaenzungsModus } from './typen'

export interface ErgaenzungsAnfrage {
  text_vor: string
  text_nach?: string
  modus?: ErgaenzungsModus
  profil_id?: string
  max_vorschlaege?: number
  seite?: { host: string; feld_art: string; sprach_hinweis: string }
}

export function ergaenze(
  anfrage: ErgaenzungsAnfrage,
  signal?: AbortSignal,
): Promise<ErgaenzungsAntwort> {
  return requestJson<ErgaenzungsAntwort>('/api/complete', {
    method: 'POST',
    body: JSON.stringify(anfrage),
    signal,
  })
}

export interface LernSignal {
  uebernommen_text: string
  uebernommen_engine: string
  text_vor?: string
  profil_id?: string
  teil_uebernahme?: boolean
  seite?: { host: string; feld_art: string; sprach_hinweis: string }
}

export function lerne(signal: LernSignal): Promise<{ gelernt: boolean; hinweis: string }> {
  return requestJson<{ gelernt: boolean; hinweis: string }>('/api/learn', {
    method: 'POST',
    body: JSON.stringify(signal),
  })
}
