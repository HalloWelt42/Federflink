/**
 * Theme-Verwaltung: Mittelton (Standard), Hell, Dunkel. Der aktive Wert liegt
 * als data-theme am Wurzelelement und wird in localStorage gemerkt.
 */

export type Theme = 'mittelton' | 'hell' | 'dunkel'

const SCHLUESSEL = 'federflink-theme'
const REIHENFOLGE: Theme[] = ['mittelton', 'hell', 'dunkel']

export const themeZustand = $state<{ aktuell: Theme }>({ aktuell: 'mittelton' })

function anwenden(theme: Theme): void {
  document.documentElement.setAttribute('data-theme', theme)
}

export function initTheme(): void {
  const gespeichert = localStorage.getItem(SCHLUESSEL) as Theme | null
  const theme: Theme = gespeichert && REIHENFOLGE.includes(gespeichert) ? gespeichert : 'mittelton'
  themeZustand.aktuell = theme
  anwenden(theme)
}

export function setzeTheme(theme: Theme): void {
  themeZustand.aktuell = theme
  anwenden(theme)
  localStorage.setItem(SCHLUESSEL, theme)
}

export function naechstesTheme(): void {
  const i = REIHENFOLGE.indexOf(themeZustand.aktuell)
  setzeTheme(REIHENFOLGE[(i + 1) % REIHENFOLGE.length])
}
