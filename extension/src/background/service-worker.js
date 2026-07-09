/**
 * Federflink Service-Worker (MV3).
 *
 * Besitzt das Netzwerk: er ruft den lokalen Server (SSE) und leitet die Frames
 * über einen langlebigen Port an das Content-Skript. Außerdem: Lernsignale,
 * Zustandsabfrage für Popup/Optionen, globaler Schalter (Kurzbefehl) und Badge.
 * Das Netzwerk läuft hier, weil Content-Skript-Anfragen der Seiten-CORS
 * unterliegen würden - der Worker-Ursprung wird vom Server erlaubt.
 */
// Gemeinsame Standardwerte laden. importScripts mit chrome.runtime.getURL kann in
// MV3 scheitern - dann wuerde der Worker sterben und nie Nachrichten verarbeiten.
// Daher robust: relativer Pfad + Notfall-Inline-Standardwerte.
try {
  importScripts('/shared/defaults.js')
} catch (e) {
  console.error('[Federflink] defaults.js nicht geladen:', e)
}
if (!self.FEDERFLINK_DEFAULTS) {
  self.FEDERFLINK_DEFAULTS = {
    aktiv: true,
    serverUrl: 'http://localhost:8500',
    profilStandard: 'standard',
    modus: 'phrase',
    minZeichen: 3,
    debounceMs: 180,
    anzeigeModus: 'auto',
    proSeite: {},
  }
  self.ffMerge = (g) => Object.assign({}, self.FEDERFLINK_DEFAULTS, g || {})
  self.ffLadeOptionen = () =>
    new Promise((r) => chrome.storage.sync.get('optionen', (d) => r(self.ffMerge(d && d.optionen))))
  self.ffSpeichereOptionen = (o) => new Promise((r) => chrome.storage.sync.set({ optionen: o }, r))
}

// ----- Vervollständigung streamen (pro Port ein Abbruch-Controller) -----
const abbruch = new WeakMap()

chrome.runtime.onConnect.addListener((port) => {
  if (port.name !== 'federflink') return
  port.onMessage.addListener((nachricht) => {
    if (nachricht.typ === 'complete') {
      const alter = abbruch.get(port)
      if (alter) alter.abort()
      const controller = new AbortController()
      abbruch.set(port, controller)
      streameVervollstaendigung(port, nachricht, controller.signal)
    } else if (nachricht.typ === 'abbruch') {
      abbruch.get(port)?.abort()
    } else if (nachricht.typ === 'lerne') {
      sendeLernsignal(nachricht.serverUrl, nachricht.signal)
    }
  })
  port.onDisconnect.addListener(() => {
    abbruch.get(port)?.abort()
    abbruch.delete(port)
  })
})

async function streameVervollstaendigung(port, nachricht, signal) {
  const { id, anfrage, serverUrl } = nachricht
  try {
    const antwort = await fetch(`${serverUrl.replace(/\/$/, '')}/api/complete`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', Accept: 'text/event-stream' },
      body: JSON.stringify(anfrage),
      signal,
    })
    if (!antwort.ok || !antwort.body) {
      console.warn('[Federflink] Server antwortete mit HTTP', antwort.status)
      sicherSenden(port, { typ: 'fehler', id, meldung: `HTTP ${antwort.status}` })
      return
    }
    const leser = antwort.body.getReader()
    const dekoder = new TextDecoder()
    let puffer = ''
    for (;;) {
      const { done, value } = await leser.read()
      if (done) break
      puffer += dekoder.decode(value, { stream: true })
      let grenze
      while ((grenze = puffer.indexOf('\n\n')) >= 0) {
        const roh = puffer.slice(0, grenze)
        puffer = puffer.slice(grenze + 2)
        weiterleiten(port, id, roh)
      }
    }
    sicherSenden(port, { typ: 'done', id })
  } catch (e) {
    if (e && e.name === 'AbortError') return
    console.warn('[Federflink] Server nicht erreichbar (', serverUrl, '):', String(e))
    sicherSenden(port, { typ: 'fehler', id, meldung: String(e) })
  }
}

function weiterleiten(port, id, roh) {
  let event = 'message'
  let daten = ''
  for (const zeile of roh.split('\n')) {
    if (zeile.startsWith('event:')) event = zeile.slice(6).trim()
    else if (zeile.startsWith('data:')) daten += zeile.slice(5).trim()
  }
  if (!daten) return
  let obj
  try {
    obj = JSON.parse(daten)
  } catch {
    return
  }
  if (event === 'instant') sicherSenden(port, { typ: 'instant', id, vorschlaege: obj.vorschlaege || [] })
  else if (event === 'token') sicherSenden(port, { typ: 'token', id, delta: obj.delta || '' })
  else if (event === 'upgrade') sicherSenden(port, { typ: 'upgrade', id, vorschlaege: obj.vorschlaege || [] })
}

function sicherSenden(port, nachricht) {
  try {
    port.postMessage(nachricht)
  } catch {
    /* Port kann bereits getrennt sein */
  }
}

async function sendeLernsignal(serverUrl, signal) {
  try {
    await fetch(`${serverUrl.replace(/\/$/, '')}/api/learn`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(signal),
    })
  } catch {
    /* Lernen ist optional - Fehler ignorieren */
  }
}

// ----- Zustandsabfrage für Popup/Optionen -----------------------------
chrome.runtime.onMessage.addListener((nachricht, _absender, antworten) => {
  if (nachricht.typ === 'zustand') {
    holeZustand(nachricht.serverUrl).then(antworten)
    return true // asynchrone Antwort
  }
  return false
})

async function holeZustand(serverUrl) {
  const basis = (serverUrl || self.FEDERFLINK_DEFAULTS.serverUrl).replace(/\/$/, '')
  try {
    const cap = await fetch(`${basis}/api/capabilities`)
    if (!cap.ok) return { online: false }
    const daten = await cap.json()
    return { online: true, capabilities: daten }
  } catch {
    return { online: false }
  }
}

// ----- Globaler Schalter (Kurzbefehl) und Badge ------------------------
chrome.commands.onCommand.addListener(async (befehl) => {
  if (befehl !== 'kill-switch') return
  const opt = await self.ffLadeOptionen()
  opt.aktiv = !opt.aktiv
  await self.ffSpeichereOptionen(opt)
  aktualisiereBadge(opt.aktiv)
})

chrome.storage.onChanged.addListener((aenderungen, bereich) => {
  if (bereich === 'sync' && aenderungen.optionen) {
    aktualisiereBadge(self.ffMerge(aenderungen.optionen.newValue).aktiv)
  }
})

function aktualisiereBadge(aktiv) {
  chrome.action.setBadgeText({ text: aktiv ? '' : 'OFF' })
  chrome.action.setBadgeBackgroundColor({ color: '#7e403c' })
  chrome.action.setTitle({ title: aktiv ? 'Federflink (aktiv)' : 'Federflink (ausgeschaltet)' })
}

chrome.runtime.onInstalled.addListener(async () => {
  aktualisiereBadge((await self.ffLadeOptionen()).aktiv)
})
chrome.runtime.onStartup.addListener(async () => {
  aktualisiereBadge((await self.ffLadeOptionen()).aktiv)
})
