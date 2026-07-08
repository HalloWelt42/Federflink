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

export interface StreamRueckrufe {
  beiInstant?: (vorschlaege: import('./typen').Vorschlag[]) => void
  beiToken?: (delta: string) => void
  beiUpgrade?: (vorschlaege: import('./typen').Vorschlag[]) => void
  beiEnde?: () => void
  beiFehler?: (fehler: unknown) => void
}

/**
 * Textergaenzung per Server-Sent-Events (Progressive Enhancement): erst der
 * Instant-Vorschlag, dann - falls ein Sprachmodell laeuft - Token und das finale
 * Upgrade. Bricht sauber ab, wenn das Signal abgebrochen wird.
 */
export async function ergaenzeStream(
  anfrage: ErgaenzungsAnfrage,
  rueckrufe: StreamRueckrufe,
  signal?: AbortSignal,
): Promise<void> {
  try {
    const antwort = await fetch('/api/complete', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'text/event-stream' },
      body: JSON.stringify(anfrage),
      signal,
    })
    if (!antwort.body) return
    const leser = antwort.body.getReader()
    const dekoder = new TextDecoder()
    let puffer = ''
    for (;;) {
      const { done, value } = await leser.read()
      if (done) break
      puffer += dekoder.decode(value, { stream: true })
      let grenze: number
      while ((grenze = puffer.indexOf('\n\n')) >= 0) {
        const roh = puffer.slice(0, grenze)
        puffer = puffer.slice(grenze + 2)
        verarbeiteFrame(roh, rueckrufe)
      }
    }
    rueckrufe.beiEnde?.()
  } catch (e) {
    if (e instanceof DOMException && e.name === 'AbortError') return
    rueckrufe.beiFehler?.(e)
  }
}

function verarbeiteFrame(roh: string, rueckrufe: StreamRueckrufe): void {
  let event = 'message'
  let daten = ''
  for (const zeile of roh.split('\n')) {
    if (zeile.startsWith('event:')) event = zeile.slice(6).trim()
    else if (zeile.startsWith('data:')) daten += zeile.slice(5).trim()
  }
  if (!daten) return
  let obj: { vorschlaege?: import('./typen').Vorschlag[]; delta?: string }
  try {
    obj = JSON.parse(daten)
  } catch {
    return
  }
  if (event === 'instant') rueckrufe.beiInstant?.(obj.vorschlaege ?? [])
  else if (event === 'token') rueckrufe.beiToken?.(obj.delta ?? '')
  else if (event === 'upgrade') rueckrufe.beiUpgrade?.(obj.vorschlaege ?? [])
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
