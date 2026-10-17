/**
 * Neue Fassung auf dem Server: nie ein hartes Neuladen verlangen.
 * Die Startseite kommt ohne Zwischenspeicher, Skripte und Gestaltung tragen Prüfsummen im Namen. Meldet der Server
 * eine andere Fassung als die eingebaute, lädt die Seite von selbst neu: in den ersten Sekunden nach dem Start sofort,
 * später beim nächsten Reiterwechsel oder wenn das Fenster wieder nach vorn kommt. Nie, solange eine Ansicht meldet,
 * dass ein Neuladen etwas abbräche (laufende Anfrage, eigener Text im Eingabefeld); dann wartet sie bis danach.
 * Dazwischen steht ein Band mit Knopf. Je Server-Fassung nur ein selbsttätiger Versuch (Merker in der Sitzung),
 * damit ein hängender Zwischenspeicher keine Schleife auslöst.
 */

import { ladeHealth } from '../api/system'

export const OBERFLAECHE_FASSUNG = __FASSUNG__
const MERKER = 'federflink.neu_geladen'
const START_FENSTER_MS = 10_000
const PRUEFEN_MS = 60_000

export const fassung = $state<{ neu: string | null }>({ neu: null })

export type Anlass = 'start' | 'takt' | 'ortswechsel' | 'sichtbar'

// Jede Ansicht meldet hier, ob ein Neuladen gerade etwas abbräche.
const taetigkeiten = new Set<() => boolean>()

/** Meldet eine Prüfung "ist gerade etwas im Gange"; die Rückgabe meldet sie wieder ab (für onMount). */
export function neuLadenAufhalten(beschaeftigt: () => boolean): () => void {
  taetigkeiten.add(beschaeftigt)
  return () => {
    taetigkeiten.delete(beschaeftigt)
  }
}

/** Nichts, was ein Neuladen abbrechen würde. */
export function ruhig(): boolean {
  for (const beschaeftigt of taetigkeiten) if (beschaeftigt()) return false
  return true
}

function erlaubt(neu: string): boolean {
  try {
    if (sessionStorage.getItem(MERKER) === neu) return false
    sessionStorage.setItem(MERKER, neu)
  } catch {
    // ohne Sitzungsspeicher kein Merker: dann lieber einmal laden als nie
  }
  return true
}

export function vielleichtNeuLaden(anlass: Anlass): void {
  const neu = fassung.neu
  if (!neu || anlass === 'takt' || !ruhig()) return
  if (anlass === 'start' && performance.now() > START_FENSTER_MS) return
  if (erlaubt(neu)) location.reload()
}

export async function fassungPruefen(anlass: Anlass): Promise<void> {
  try {
    const server = (await ladeHealth()).version
    fassung.neu = server !== OBERFLAECHE_FASSUNG ? server : null
  } catch {
    return // ohne Verbindung meldet die Statuszeile das Backend als nicht erreichbar
  }
  vielleichtNeuLaden(anlass)
}

function sichtbar(): void {
  if (document.visibilityState === 'visible') void fassungPruefen('sichtbar')
}

export function fassungVerfolgen(): () => void {
  void fassungPruefen('start')
  const takt = setInterval(() => void fassungPruefen('takt'), PRUEFEN_MS)
  document.addEventListener('visibilitychange', sichtbar)
  return () => {
    clearInterval(takt)
    document.removeEventListener('visibilitychange', sichtbar)
  }
}
