/**
 * Federflink Content-Skript (ISOLATED world).
 *
 * Beobachtet Eingabefelder, holt beim Tippen (entprellt) eine Ergänzung über
 * den Service-Worker (SSE) und zeigt sie als Vorschau: Inline-Geistertext in
 * input/textarea (nur am Textende), sonst eine schwebende Pille. Tab übernimmt,
 * Esc verwirft. Nichts wird automatisch eingefügt. Passwort-/Sensibelfelder
 * werden nie ausgelesen.
 */
;(() => {
  'use strict'
  if (window.__federflinkGeladen) return
  window.__federflinkGeladen = true

  const NS = '__FEDERFLINK__'
  const HOST = location.hostname

  // Diagnose (Statusbox oben rechts + Konsolen-Logs). Zum Debuggen auf true setzen.
  const DEBUG = false
  const flog = (...a) => {
    if (DEBUG) console.log('%c[Federflink]', 'color:#2f6154;font-weight:bold', ...a)
  }

  // Sichtbare Statusanzeige oben rechts (nur bei DEBUG) - zeigt live, was passiert.
  let statusEl = null
  function setzeStatus(text, fehlerhaft) {
    if (!DEBUG) return
    if (!statusEl) {
      statusEl = document.createElement('div')
      statusEl.style.cssText =
        'all:initial; position:fixed; top:8px; right:8px; z-index:2147483647;' +
        'font:12px/1.4 system-ui,-apple-system,sans-serif; background:#1f2624;' +
        'padding:6px 10px; border-radius:6px; box-shadow:0 2px 10px rgba(0,0,0,.45);' +
        'max-width:340px; opacity:.94; pointer-events:none; white-space:normal;'
      ;(document.body || document.documentElement).appendChild(statusEl)
    }
    let v = '?'
    try {
      v = (chrome.runtime.getManifest && chrome.runtime.getManifest().version) || '?'
    } catch {
      /* Kontext ungueltig */
    }
    statusEl.style.color = fehlerhaft ? '#ff9a8a' : '#9be6c8'
    statusEl.textContent = `Federflink ${v} · ${text}`
  }

  // Notfall-Standardwerte, falls shared/defaults.js nicht (rechtzeitig) geladen wurde.
  if (!self.FEDERFLINK_DEFAULTS) {
    console.error('[Federflink] defaults.js nicht geladen - Notfall-Standardwerte aktiv')
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
    self.ffSeite = (opt, host) => {
      const e = (opt.proSeite && opt.proSeite[host]) || {}
      return { aktiv: e.aktiv !== false, profil: e.profil || opt.profilStandard, lernen: e.lernen === true }
    }
    self.ffLadeOptionen = () => Promise.resolve(self.ffMerge())
  }

  let optionen = self.FEDERFLINK_DEFAULTS
  let seite = { aktiv: true, profil: 'standard', lernen: false }
  flog('Content-Skript aktiv auf', HOST, '- Server:', optionen.serverUrl)
  setzeStatus('geladen auf ' + HOST + ' - jetzt in ein Textfeld klicken')

  let feld = null // aktuelles bearbeitbares Feld
  let anfrageNr = 0 // monoton, gegen veraltete Antworten
  let aktiverVorschlag = null // { text, engine }
  let alternativen = []
  let entprellungs = null
  let mainInjiziert = false

  // True, solange die Erweiterung nicht neu geladen wurde (sonst ist chrome.runtime.id weg).
  const kontextOk = () => {
    try {
      return !!(chrome.runtime && chrome.runtime.id)
    } catch {
      return false
    }
  }

  // ----- Optionen laden und aktuell halten -------------------------------
  try {
    self.ffLadeOptionen().then((o) => {
      optionen = o
      seite = self.ffSeite(o, HOST)
    })
    chrome.storage.onChanged.addListener((aenderungen, bereich) => {
      if (bereich === 'sync' && aenderungen.optionen) {
        optionen = self.ffMerge(aenderungen.optionen.newValue)
        seite = self.ffSeite(optionen, HOST)
        if (!istGlobalAktiv()) verstecken()
      }
    })
  } catch {
    // "Extension context invalidated": altes Content-Skript nach Reload der Erweiterung.
    setzeStatus('Erweiterung wurde neu geladen - bitte diese Seite aktualisieren (F5)', true)
  }

  const istGlobalAktiv = () => optionen.aktiv && seite.aktiv

  // ----- Service-Worker-Port ---------------------------------------------
  let port = null
  function holePort() {
    if (port) return port
    if (!kontextOk()) return null
    try {
      port = chrome.runtime.connect({ name: 'federflink' })
      port.onMessage.addListener(behandleFrame)
      port.onDisconnect.addListener(() => {
        port = null
      })
      return port
    } catch {
      return null
    }
  }

  function behandleFrame(frame) {
    if (frame.typ === 'fehler') {
      flog('Server-Fehler:', frame.meldung, '- laeuft der Server auf', optionen.serverUrl, '?')
      setzeStatus('Server nicht erreichbar unter ' + optionen.serverUrl + ' (' + frame.meldung + ')', true)
      return
    }
    if (frame.id !== anfrageNr) return // veraltete Antwort verwerfen
    if (frame.typ === 'instant') {
      const vs = frame.vorschlaege || []
      flog('Instant-Antwort:', vs.length, 'Vorschlag/Vorschlaege', vs[0] ? `("${vs[0].text}")` : '')
      setzeStatus(vs.length + ' Vorschlag(e)' + (vs[0] ? ': "' + vs[0].text + '"' : ' (nichts fuer diesen Text)'))
      aktiverVorschlag = vs[0] || null
      alternativen = vs.slice(1)
      rendern()
    } else if (frame.typ === 'upgrade') {
      const vs = frame.vorschlaege || []
      if (vs[0]) {
        if (aktiverVorschlag) alternativen = [aktiverVorschlag, ...alternativen].slice(0, 3)
        aktiverVorschlag = vs[0]
        rendern()
      }
    }
  }

  // ----- Feld-Eignung und Datenschutz ------------------------------------
  const TEXT_TYPEN = new Set(['text', 'search', ''])
  const SENSIBEL = /pass|pwd|otp|pin|cvv|cvc|card|iban|ssn|secret|token|2fa|mfa|geheim|kennwort/i

  function istBearbeitbar(el) {
    if (!el) return false
    if (el.isContentEditable) return true
    const tag = el.tagName
    if (tag === 'TEXTAREA') return true
    if (tag === 'INPUT') {
      const typ = (el.getAttribute('type') || '').toLowerCase()
      return TEXT_TYPEN.has(typ)
    }
    return false
  }

  function istSensibel(el) {
    if (el.tagName === 'INPUT') {
      const typ = (el.getAttribute('type') || '').toLowerCase()
      if (typ === 'password' || typ === 'hidden') return true
      const ac = (el.getAttribute('autocomplete') || '').toLowerCase()
      if (/password|one-time-code|cc-|current-|new-password/.test(ac)) return true
    }
    const merkmale = `${el.name || ''} ${el.id || ''} ${el.getAttribute('aria-label') || ''}`
    if (SENSIBEL.test(merkmale)) return true
    if (el.dataset && el.dataset.federflinkOff !== undefined) return true
    // Feld im selben Formular wie ein Passwortfeld -> nicht anfassen.
    const formular = el.form
    if (formular && formular.querySelector('input[type="password"]')) return true
    return false
  }

  function eignet(el) {
    return istBearbeitbar(el) && !istSensibel(el)
  }

  // Textknoten, die zu Platzhaltern/Dekoration gehoeren (Discord/Slate rendert den
  // Platzhalter als echtes DOM-Element) - die duerfen nicht als Inhalt zaehlen.
  function istDekoKnoten(wurzel, node) {
    let el = node.parentElement
    while (el && el !== wurzel) {
      if (
        el.hasAttribute('data-placeholder') ||
        el.hasAttribute('data-slate-placeholder') ||
        el.getAttribute('aria-hidden') === 'true' ||
        el.getAttribute('contenteditable') === 'false'
      ) {
        return true
      }
      el = el.parentElement
    }
    return false
  }

  // Sammelt den echten Editortext vor dem Cursor und gesamt (ohne Platzhalter).
  function sammleEditorKontext(wurzel, bereich) {
    const walker = document.createTreeWalker(wurzel, NodeFilter.SHOW_TEXT)
    let vor = ''
    let gesamt = ''
    let n
    while ((n = walker.nextNode())) {
      if (istDekoKnoten(wurzel, n)) continue
      const t = n.textContent || ''
      gesamt += t
      let cpEnde
      try {
        cpEnde = bereich.comparePoint(n, t.length)
      } catch {
        cpEnde = 1
      }
      if (cpEnde <= 0) {
        vor += t // ganzer Knoten liegt vor dem Cursor
      } else if (n === bereich.endContainer) {
        vor += t.slice(0, bereich.endOffset) // Cursor liegt in diesem Knoten
      }
    }
    return { vor, gesamt }
  }

  // ----- Kontext am Cursor holen -----------------------------------------
  function kontext() {
    if (!feld) return null
    if (feld.tagName === 'INPUT' || feld.tagName === 'TEXTAREA') {
      const start = feld.selectionStart ?? feld.value.length
      const ende = feld.selectionEnd ?? start
      return {
        vor: feld.value.slice(0, start),
        nach: feld.value.slice(ende),
        start,
        ende,
        amEnde: ende === feld.value.length,
        feldArt: feld.tagName === 'TEXTAREA' ? 'textarea' : 'input',
      }
    }
    // contenteditable
    const auswahl = window.getSelection()
    if (!auswahl || auswahl.rangeCount === 0) return null
    const bereich = auswahl.getRangeAt(0)
    if (!feld.contains(bereich.endContainer)) return null
    const { vor, gesamt } = sammleEditorKontext(feld, bereich)
    return {
      vor,
      nach: gesamt.slice(vor.length),
      amEnde: bereich.collapsed && vor.length >= gesamt.length,
      feldArt: 'contenteditable',
    }
  }

  // ----- Anfrage stellen (entprellt) -------------------------------------
  function planen() {
    clearTimeout(entprellungs)
    entprellungs = setTimeout(anfordern, optionen.debounceMs)
  }

  function anfordern() {
    if (!feld || !istGlobalAktiv() || !eignet(feld)) {
      flog('keine Anfrage - Feld:', !!feld, 'global aktiv:', istGlobalAktiv())
      return
    }
    const k = kontext()
    if (!k || k.vor.trim().length < optionen.minZeichen) {
      flog('keine Anfrage - zu wenig Text (', k ? k.vor.trim().length : 0, 'von', optionen.minZeichen, ')')
      verstecken()
      return
    }
    anfrageNr += 1
    aktiverVorschlag = null
    alternativen = []
    const anfrage = {
      request_id: String(anfrageNr),
      text_vor: k.vor.slice(-optionen.minZeichen - 800),
      text_nach: k.nach.slice(0, 200),
      modus: optionen.modus,
      profil_id: seite.profil,
      max_vorschlaege: 3,
      seite: { host: HOST, feld_art: k.feldArt, sprach_hinweis: 'de' },
    }
    const p = holePort()
    if (!p) {
      setzeStatus('Erweiterung wurde neu geladen - bitte diese Seite aktualisieren (F5)', true)
      return
    }
    flog('Anfrage', anfrageNr, 'gesendet, Kontext endet mit:', JSON.stringify(k.vor.slice(-25)))
    setzeStatus('Anfrage ' + anfrageNr + ' an Server gesendet …')
    p.postMessage({ typ: 'complete', id: anfrageNr, anfrage, serverUrl: optionen.serverUrl })
  }

  // ----- Overlay: Shadow-Host --------------------------------------------
  let shadowHost = null
  let schatten = null
  function baueHost() {
    if (shadowHost) return
    shadowHost = document.createElement('div')
    // top/left/size MUESSEN gesetzt sein: ein position:fixed-Element ohne top/left
    // sitzt an seiner statischen Position (weit unten bei langen Seiten), wodurch
    // die absolut positionierten Overlays ausserhalb des Sichtbereichs landen.
    shadowHost.style.cssText =
      'all:initial; position:fixed; top:0; left:0; width:0; height:0; z-index:2147483646; pointer-events:none;'
    schatten = shadowHost.attachShadow({ mode: 'open' })
    schatten.innerHTML = `
      <style>
        .spiegel{ position:absolute; overflow:hidden; box-sizing:border-box; color:transparent;
          background:transparent; pointer-events:none; margin:0; }
        /* im normalen Fluss (nicht absolut), damit der Text nach dem Padding beginnt
           wie im echten Feld; das translate gleicht nur den Scroll aus. */
        .spiegel .inner{ position:relative; margin:0; }
        .geist{ color: rgba(120,120,120,0.85); }
        .geist-frei{ position:absolute; pointer-events:none; white-space:pre;
          display:flex; align-items:center; gap:4px; overflow:hidden; }
        .geist-frei .geist{ color: rgba(155,155,155,0.95); }
        .geist-frei .taste{ color: rgba(155,155,155,0.65); font-size:0.72em; line-height:1.2;
          border:1px solid rgba(155,155,155,0.45); border-radius:3px; padding:0 3px; }
      </style>`
    document.documentElement.appendChild(shadowHost)
  }

  // Nur die Overlay-Elemente aus dem Schatten-DOM entfernen (Zustand bleibt).
  function overlayLeeren() {
    if (schatten) {
      const alt = schatten.querySelectorAll('.spiegel, .geist-frei')
      alt.forEach((n) => n.remove())
    }
  }

  // Vorschau ganz verwerfen: DOM leeren UND den Zustand zuruecksetzen.
  function verstecken() {
    aktiverVorschlag = null
    alternativen = []
    overlayLeeren()
  }

  // Text-/Boxmetriken des Feldes, die der Spiegel exakt uebernehmen muss.
  // boxSizing bewusst NICHT dabei: der Spiegel bleibt border-box (siehe CSS),
  // sonst verschoebe sich die Ausrichtung je nach Feld.
  const STIL_FELDER = [
    'fontFamily', 'fontSize', 'fontWeight', 'fontStyle', 'fontVariant', 'letterSpacing',
    'wordSpacing', 'lineHeight', 'textTransform', 'textIndent', 'textAlign', 'tabSize',
    'paddingTop', 'paddingRight', 'paddingBottom', 'paddingLeft', 'borderTopWidth',
    'borderRightWidth', 'borderBottomWidth', 'borderLeftWidth', 'direction',
  ]

  function rendern() {
    overlayLeeren() // nur alte Overlay-Elemente entfernen, Vorschlag NICHT loeschen
    if (!feld || !aktiverVorschlag) return
    const ghost = aktiverVorschlag.text
    if (!ghost) return
    const k = kontext()
    if (!k) return
    baueHost()

    const inline =
      (feld.tagName === 'INPUT' || feld.tagName === 'TEXTAREA') &&
      k.amEnde &&
      optionen.anzeigeModus !== 'pille'
    flog('rendern:', inline ? 'inline-Geistertext (Spiegel)' : 'Geistertext am Cursor', '->', JSON.stringify(ghost))
    setzeStatus('Geistertext gezeigt (' + (inline ? 'inline' : 'am Cursor') + '): "' + ghost + '" - Tab uebernimmt')
    if (inline) {
      zeigeInline(ghost, k)
    } else {
      zeigeGeistAmCursor(ghost, k)
    }
  }

  function zeigeInline(ghost, k) {
    const rect = feld.getBoundingClientRect()
    const stil = getComputedStyle(feld)
    const spiegel = document.createElement('div')
    spiegel.className = 'spiegel'
    spiegel.style.left = rect.left + 'px'
    spiegel.style.top = rect.top + 'px'
    spiegel.style.width = rect.width + 'px'
    spiegel.style.height = rect.height + 'px'
    STIL_FELDER.forEach((f) => (spiegel.style[f] = stil[f]))
    spiegel.style.borderStyle = 'solid'
    spiegel.style.borderColor = 'transparent'
    if (feld.tagName === 'TEXTAREA') {
      spiegel.style.whiteSpace = 'pre-wrap'
      spiegel.style.overflowWrap = 'break-word'
    } else {
      spiegel.style.whiteSpace = 'pre'
    }
    const inner = document.createElement('div')
    inner.className = 'inner'
    inner.style.transform = `translate(${-feld.scrollLeft}px, ${-feld.scrollTop}px)`
    const pre = document.createElement('span')
    pre.textContent = k.vor
    const g = document.createElement('span')
    g.className = 'geist'
    g.textContent = ghost
    inner.appendChild(pre)
    inner.appendChild(g)
    spiegel.appendChild(inner)
    schatten.appendChild(spiegel)
  }

  // Grauer Geistertext direkt am Cursor (contenteditable und mid-line-Faelle).
  // Sitzt auf der Cursor-Zeile - dadurch kein Problem, wenn das Feld am unteren
  // Bildrand liegt (Discord/Twitch). Beruehrt den Editor-DOM nicht.
  function zeigeGeistAmCursor(ghost, k) {
    const m = caretMetrik(k)
    const stil = getComputedStyle(feld)
    const el = document.createElement('div')
    el.className = 'geist-frei'
    el.style.left = m.x + 'px'
    el.style.top = m.y + 'px'
    el.style.height = m.h + 'px'
    el.style.lineHeight = m.h + 'px'
    el.style.fontFamily = stil.fontFamily
    el.style.fontSize = stil.fontSize
    el.style.fontWeight = stil.fontWeight
    el.style.maxWidth = Math.max(60, window.innerWidth - m.x - 8) + 'px'

    const t = document.createElement('span')
    t.className = 'geist'
    t.textContent = ghost
    const hint = document.createElement('span')
    hint.className = 'taste'
    hint.textContent = '⇥'
    el.appendChild(t)
    el.appendChild(hint)
    schatten.appendChild(el)
  }

  // Cursor-Metrik (Viewport): x/y der Cursor-Oberkante + Zeilenhoehe h.
  function caretMetrik(k) {
    if (feld.tagName === 'INPUT' || feld.tagName === 'TEXTAREA') {
      const rect = feld.getBoundingClientRect()
      const stil = getComputedStyle(feld)
      const mess = document.createElement('div')
      const st = mess.style
      st.position = 'absolute'
      st.visibility = 'hidden'
      st.whiteSpace = feld.tagName === 'TEXTAREA' ? 'pre-wrap' : 'pre'
      st.overflowWrap = 'break-word'
      st.boxSizing = 'border-box'
      st.borderStyle = 'solid'
      st.borderColor = 'transparent'
      st.width = rect.width + 'px'
      STIL_FELDER.forEach((f) => (st[f] = stil[f]))
      mess.textContent = k.vor
      const marke = document.createElement('span')
      marke.textContent = '​'
      mess.appendChild(marke)
      document.body.appendChild(mess)
      const mrect = marke.getBoundingClientRect()
      const brect = mess.getBoundingClientRect()
      const x = rect.left + (mrect.left - brect.left) - feld.scrollLeft
      const y = rect.top + (mrect.top - brect.top) - feld.scrollTop
      const h = mrect.height || parseFloat(stil.lineHeight) || parseFloat(stil.fontSize) * 1.3
      document.body.removeChild(mess)
      return { x, y, h }
    }
    // contenteditable: Cursor-Rechteck aus der Selektion (ohne den Editor-DOM zu aendern).
    const auswahl = window.getSelection()
    if (auswahl && auswahl.rangeCount) {
      const bereich = auswahl.getRangeAt(0)
      let r = bereich.getBoundingClientRect()
      if (!r.width && !r.height && !r.top && !r.left) {
        const rects = bereich.getClientRects()
        if (rects && rects.length) r = rects[rects.length - 1]
      }
      if (r && !r.height && !r.top && !r.left) {
        const knoten = bereich.startContainer
        const eln = knoten.nodeType === 1 ? knoten : knoten.parentElement
        if (eln) r = eln.getBoundingClientRect()
      }
      if (r && (r.height || r.top || r.left)) {
        return { x: r.right || r.left, y: r.top, h: r.height || 18 }
      }
    }
    const b = feld.getBoundingClientRect()
    return { x: b.left, y: b.top, h: 18 }
  }

  // ----- Übernehmen / Verwerfen -----------------------------------------
  function injiziereMain() {
    if (mainInjiziert) return
    mainInjiziert = true
    try {
      const s = document.createElement('script')
      s.src = chrome.runtime.getURL('src/content/ghost-inject.js')
      s.onload = () => s.remove()
      ;(document.head || document.documentElement).appendChild(s)
    } catch {
      /* CSP kann Injektion verhindern - dann greift der Content-Fallback */
    }
  }

  function uebernehmen(vorschlag) {
    if (!feld || !vorschlag) return
    const k = kontext()
    if (!k) return
    const ghost = vorschlag.text

    if (feld.tagName === 'INPUT' || feld.tagName === 'TEXTAREA') {
      const neu = k.vor + ghost + k.nach
      const cursor = (k.vor + ghost).length
      // Bevorzugt über die Seitenwelt (Framework-sicher); Fallback im Content.
      window.postMessage({ ns: NS, typ: 'einfuegen', wert: neu, cursor }, '*')
      setTimeout(() => {
        if (feld && feld.value !== neu) {
          feld.value = neu
          feld.dispatchEvent(new Event('input', { bubbles: true }))
          try {
            feld.setSelectionRange(cursor, cursor)
          } catch {
            /* egal */
          }
        }
      }, 0)
    } else if (feld.isContentEditable) {
      feld.focus()
      document.execCommand('insertText', false, ghost)
    }

    lerne(vorschlag, k)
    verstecken()
    setTimeout(planen, 30)
  }

  function lerne(vorschlag, k) {
    const p = holePort()
    if (!p) return
    p.postMessage({
      typ: 'lerne',
      serverUrl: optionen.serverUrl,
      signal: {
        uebernommen_text: vorschlag.text,
        uebernommen_engine: vorschlag.engine,
        // Kontext nur senden, wenn pro Seite ausdrücklich erlaubt (Datenschutz).
        text_vor: seite.lernen ? k.vor : null,
        profil_id: seite.profil,
        seite: { host: HOST, feld_art: k.feldArt, sprach_hinweis: 'de' },
      },
    })
  }

  function teilUebernehmen() {
    if (!aktiverVorschlag) return
    const treffer = aktiverVorschlag.text.match(/^\s*\S+/)
    if (!treffer) return
    uebernehmen({ text: treffer[0], engine: aktiverVorschlag.engine })
  }

  // ----- Tasten (Capture, um Seite/Editor zuvorzukommen) -----------------
  document.addEventListener(
    'keydown',
    (e) => {
      if (!aktiverVorschlag || e.target !== feld) return
      if (e.isComposing) return
      if (e.key === 'Tab') {
        e.preventDefault()
        e.stopImmediatePropagation()
        uebernehmen(aktiverVorschlag)
      } else if (e.key === 'Escape') {
        e.preventDefault()
        verstecken()
      } else if ((e.ctrlKey || e.altKey) && e.key === 'ArrowRight') {
        e.preventDefault()
        teilUebernehmen()
      } else if (e.key.startsWith('Arrow') || e.key === 'Home' || e.key === 'End') {
        verstecken()
      }
    },
    true,
  )

  // ----- Fokus / Eingabe / Verwerfen -------------------------------------
  // Bei contenteditable auf den obersten editierbaren Container klettern
  // (Discord/Slate fokussiert oft einen inneren Knoten).
  function editHost(el) {
    let n = el
    while (n && n.parentElement && n.parentElement.isContentEditable) n = n.parentElement
    return n
  }

  document.addEventListener('focusin', (e) => {
    let ziel = e.composedPath ? e.composedPath()[0] : e.target
    if (ziel && ziel.isContentEditable) ziel = editHost(ziel)
    if (eignet(ziel)) {
      feld = ziel
      flog('Feld im Fokus:', feld.tagName, feld.type || (feld.isContentEditable ? 'contenteditable' : ''))
      setzeStatus('Feld erkannt: ' + feld.tagName + (feld.isContentEditable ? ' (contenteditable)' : '') + ' - jetzt tippen')
      injiziereMain()
    } else {
      feld = null
      verstecken()
    }
  })
  document.addEventListener('focusout', () => {
    feld = null
    verstecken()
  })
  document.addEventListener('input', (e) => {
    if (e.target === feld) planen()
  })
  // Beim Scrollen NICHT pauschal verstecken (Chat-Listen scrollen staendig und
  // wuerden den Vorschlag sofort loeschen). Nur wenn das Feld selbst mitscrollt,
  // den Geistertext neu positionieren.
  let scrollGeplant = false
  document.addEventListener(
    'scroll',
    (e) => {
      if (!aktiverVorschlag || !feld) return
      const ziel = e.target
      const betrifftFeld =
        ziel === document ||
        ziel === document.documentElement ||
        ziel === document.body ||
        (ziel.contains && ziel.contains(feld))
      if (!betrifftFeld || scrollGeplant) return
      scrollGeplant = true
      requestAnimationFrame(() => {
        scrollGeplant = false
        rendern()
      })
    },
    true,
  )
  window.addEventListener('resize', () => {
    if (aktiverVorschlag) rendern()
  })
  window.addEventListener('blur', () => verstecken())
})()
