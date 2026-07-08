/**
 * Gemeinsame Standardwerte und Helfer für Service-Worker, Content-Skript und
 * die Einstellungsseiten. Wird in allen drei Kontexten geladen und legt seine
 * Helfer auf `self` ab (kein Modul-Import, damit es überall gleich funktioniert).
 */

self.FEDERFLINK_DEFAULTS = {
  aktiv: true, // globaler Schalter (Kill-Switch)
  serverUrl: 'http://localhost:8500',
  profilStandard: 'standard',
  modus: 'phrase', // wort | phrase | satz
  minZeichen: 3,
  debounceMs: 180,
  anzeigeModus: 'auto', // auto | inline | pille
  proSeite: {}, // host -> { aktiv: bool, profil: string, lernen: bool }
}

/** Führt gespeicherte Optionen mit den Standardwerten zusammen. */
self.ffMerge = function ffMerge(gespeichert) {
  const opt = Object.assign({}, self.FEDERFLINK_DEFAULTS, gespeichert || {})
  opt.proSeite = Object.assign({}, gespeichert && gespeichert.proSeite)
  return opt
}

/** Effektive Einstellung für einen Host (mit Rückfall auf die Vorgaben). */
self.ffSeite = function ffSeite(opt, host) {
  const eintrag = (opt.proSeite && opt.proSeite[host]) || {}
  return {
    aktiv: eintrag.aktiv !== false, // Standard: an, außer ausdrücklich aus
    profil: eintrag.profil || opt.profilStandard,
    lernen: eintrag.lernen === true, // Standard: kein Kontext senden (Datenschutz)
  }
}

/** Optionen aus dem Speicher lesen (Promise). */
self.ffLadeOptionen = function ffLadeOptionen() {
  return new Promise((aufloesen) => {
    chrome.storage.sync.get('optionen', (daten) => aufloesen(self.ffMerge(daten && daten.optionen)))
  })
}

/** Optionen speichern (Promise). */
self.ffSpeichereOptionen = function ffSpeichereOptionen(optionen) {
  return new Promise((aufloesen) => {
    chrome.storage.sync.set({ optionen }, () => aufloesen())
  })
}
