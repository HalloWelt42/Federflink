/** API: Schreibprofile. */

import { requestJson } from './http'
import type { Profil } from './typen'

export function ladeProfile(): Promise<Profil[]> {
  return requestJson<Profil[]>('/api/profiles')
}

export interface ProfilAnlage {
  id: string
  name: string
  sprache?: string
  beschreibung?: string
  stil_prompt?: string
  host_muster?: string[]
}

export function legeProfilAn(anlage: ProfilAnlage): Promise<Profil> {
  return requestJson<Profil>('/api/profiles', {
    method: 'POST',
    body: JSON.stringify(anlage),
  })
}

export function entferneProfil(id: string): Promise<{ entfernt: boolean }> {
  return requestJson<{ entfernt: boolean }>(`/api/profiles/${encodeURIComponent(id)}`, {
    method: 'DELETE',
  })
}
