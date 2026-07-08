/** API: Rechtschreibprüfung und Korrektur. */

import { requestJson } from './http'
import type { KorrekturAntwort, PruefAntwort, SatzAntwort } from './typen'

export function pruefe(
  text: string,
  profilId = 'standard',
  engines?: string[],
): Promise<PruefAntwort> {
  return requestJson<PruefAntwort>('/api/spellcheck', {
    method: 'POST',
    body: JSON.stringify({ text, profil_id: profilId, engines: engines ?? null }),
  })
}

export function korrigiere(text: string, modell?: string): Promise<KorrekturAntwort> {
  return requestJson<KorrekturAntwort>('/api/correct', {
    method: 'POST',
    body: JSON.stringify({ text, modell: modell ?? null }),
  })
}

/** Bis zu drei Varianten fuer EINEN Satz (unlogisch/falsche Wortwahl), schnell. */
export function satzVorschlaege(satz: string, profilId = 'standard'): Promise<SatzAntwort> {
  return requestJson<SatzAntwort>('/api/satzvorschlaege', {
    method: 'POST',
    body: JSON.stringify({ satz, profil_id: profilId }),
  })
}
