/** API: persoenliches Woerterbuch. */

import { requestJson } from './http'
import type { WoerterbuchListe, WortEintrag } from './typen'

export function ladeWoerterbuch(profilId?: string): Promise<WoerterbuchListe> {
  const pfad = profilId ? `/api/woerterbuch?profil_id=${encodeURIComponent(profilId)}` : '/api/woerterbuch'
  return requestJson<WoerterbuchListe>(pfad)
}

export function fuegeWortHinzu(wort: string, profilId = 'standard'): Promise<WortEintrag> {
  return requestJson<WortEintrag>('/api/woerterbuch', {
    method: 'POST',
    body: JSON.stringify({ wort, profil_id: profilId }),
  })
}

export function entferneWort(wort: string, profilId = 'standard'): Promise<{ entfernt: boolean }> {
  return requestJson<{ entfernt: boolean }>('/api/woerterbuch', {
    method: 'DELETE',
    body: JSON.stringify({ wort, profil_id: profilId }),
  })
}
