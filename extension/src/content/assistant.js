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

  let optionen = self.FEDERFLINK_DEFAULTS
  let seite = { aktiv: true, profil: 'standard', lernen: false }

  let feld = null // aktuelles bearbeitbares Feld
  let anfrageNr = 0 // monoton, gegen veraltete Antworten
  let aktiverVorschlag = null // { text, engine }
  let alternativen = []
  let entprellungs = null
  let mainInjiziert = false

  // ----- Optionen laden und aktuell halten -------------------------------
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

  const istGlobalAktiv = () => optionen.aktiv && seite.aktiv

  // ----- Service-Worker-Port ---------------------------------------------
  let port = null
  function holePort() {
    if (port) return port
    port = chrome.runtime.connect({ name: 'federflink' })
    port.onMessage.addListener(behandleFrame)
    port.onDisconnect.addListener(() => {
      port = null
    })
    return port
  }

  function behandleFrame(frame) {
    if (frame.id !== anfrageNr) return // veraltete Antwort verwerfen
    if (frame.typ === 'instant') {
      const vs = frame.vorschlaege || []
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
    const vorBereich = bereich.cloneRange()
    vorBereich.selectNodeContents(feld)
    vorBereich.setEnd(bereich.endContainer, bereich.endOffset)
    const vor = vorBereich.toString()
    const gesamt = feld.textContent || ''
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
    if (!feld || !istGlobalAktiv() || !eignet(feld)) return
    const k = kontext()
    if (!k || k.vor.trim().length < optionen.minZeichen) {
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
    holePort().postMessage({ typ: 'complete', id: anfrageNr, anfrage, serverUrl: optionen.serverUrl })
  }

  // ----- Overlay: Shadow-Host --------------------------------------------
  let shadowHost = null
  let schatten = null
  function baueHost() {
    if (shadowHost) return
    shadowHost = document.createElement('div')
    shadowHost.style.cssText = 'all:initial; position:fixed; z-index:2147483646; pointer-events:none;'
    schatten = shadowHost.attachShadow({ mode: 'open' })
    schatten.innerHTML = `
      <style>
        .spiegel{ position:absolute; overflow:hidden; box-sizing:border-box; color:transparent;
          background:transparent; pointer-events:none; }
        .spiegel .inner{ position:absolute; top:0; left:0; }
        .geist{ color: rgba(120,120,120,0.85); }
        .pille{ position:absolute; pointer-events:auto; background:#2f6154; color:#f2f6f4;
          font:13px/1.4 system-ui,-apple-system,sans-serif; padding:4px 8px; border-radius:4px;
          box-shadow:0 4px 14px rgba(0,0,0,0.3); max-width:360px; white-space:pre-wrap;
          cursor:pointer; display:flex; gap:8px; align-items:center; }
        .pille .taste{ font-size:11px; opacity:0.85; border:1px solid rgba(255,255,255,0.5);
          border-radius:3px; padding:0 4px; }
      </style>`
    document.documentElement.appendChild(shadowHost)
  }

  function verstecken() {
    aktiverVorschlag = null
    alternativen = []
    if (schatten) {
      const alt = schatten.querySelectorAll('.spiegel, .pille')
      alt.forEach((n) => n.remove())
    }
  }

  const STIL_FELDER = [
    'fontFamily', 'fontSize', 'fontWeight', 'fontStyle', 'fontVariant', 'letterSpacing',
    'wordSpacing', 'lineHeight', 'textTransform', 'textIndent', 'textAlign', 'tabSize',
    'paddingTop', 'paddingRight', 'paddingBottom', 'paddingLeft', 'borderTopWidth',
    'borderRightWidth', 'borderBottomWidth', 'borderLeftWidth', 'boxSizing', 'direction',
  ]

  function rendern() {
    verstecken()
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
    if (inline && optionen.anzeigeModus !== 'pille') {
      zeigeInline(ghost, k)
    } else {
      zeigePille(ghost, k)
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

  function zeigePille(ghost, k) {
    const koord = caretKoordinaten(k)
    const pille = document.createElement('div')
    pille.className = 'pille'
    const txt = document.createElement('span')
    txt.textContent = ghost.length > 80 ? ghost.slice(0, 80) + '…' : ghost
    const taste = document.createElement('span')
    taste.className = 'taste'
    taste.textContent = 'Tab'
    pille.appendChild(txt)
    pille.appendChild(taste)
    pille.addEventListener('mousedown', (e) => {
      e.preventDefault()
      uebernehmen(aktiverVorschlag)
    })
    // Position mit Viewport-Begrenzung.
    let x = koord.x
    let y = koord.y + 20
    if (x + 370 > window.innerWidth) x = Math.max(8, window.innerWidth - 370)
    if (y + 40 > window.innerHeight) y = koord.y - 34
    pille.style.left = x + 'px'
    pille.style.top = y + 'px'
    schatten.appendChild(pille)
  }

  // Cursorkoordinaten (Viewport) für die Pille.
  function caretKoordinaten(k) {
    if (feld.tagName === 'INPUT' || feld.tagName === 'TEXTAREA') {
      const rect = feld.getBoundingClientRect()
      const stil = getComputedStyle(feld)
      const mess = document.createElement('div')
      const st = mess.style
      st.position = 'absolute'
      st.visibility = 'hidden'
      st.whiteSpace = feld.tagName === 'TEXTAREA' ? 'pre-wrap' : 'pre'
      st.overflowWrap = 'break-word'
      st.width = feld.clientWidth + 'px'
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
      document.body.removeChild(mess)
      return { x, y }
    }
    // contenteditable
    const auswahl = window.getSelection()
    if (auswahl && auswahl.rangeCount) {
      let r = auswahl.getRangeAt(0).getBoundingClientRect()
      if (r.x === 0 && r.y === 0) {
        const b = feld.getBoundingClientRect()
        return { x: b.left, y: b.top }
      }
      return { x: r.left, y: r.top }
    }
    const b = feld.getBoundingClientRect()
    return { x: b.left, y: b.top }
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
    holePort().postMessage({
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
  document.addEventListener('focusin', (e) => {
    const ziel = e.composedPath ? e.composedPath()[0] : e.target
    if (eignet(ziel)) {
      feld = ziel
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
  document.addEventListener('scroll', () => verstecken(), true)
  window.addEventListener('resize', () => verstecken())
  window.addEventListener('blur', () => verstecken())
})()
