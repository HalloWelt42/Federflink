/** API: Rechtschreibprüfung und Korrektur. */

import { requestJson } from './http'
import type { KorrekturAntwort, PruefAntwort } from './typen'

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
