/** Einstellungsseite: Server, Ergänzung, seitenspezifische Regeln. */
;(async () => {
  const $ = (id) => document.getElementById(id)
  let optionen = await self.ffLadeOptionen()
  let profile = [{ id: 'standard', name: 'Standard' }]

  // Einfache Felder füllen.
  $('serverUrl').value = optionen.serverUrl
  $('modus').value = optionen.modus
  $('anzeigeModus').value = optionen.anzeigeModus
  $('minZeichen').value = optionen.minZeichen
  $('debounceMs').value = optionen.debounceMs

  async function speichern() {
    optionen.serverUrl = $('serverUrl').value.trim() || self.FEDERFLINK_DEFAULTS.serverUrl
    optionen.profilStandard = $('profilStandard').value || 'standard'
    optionen.modus = $('modus').value
    optionen.anzeigeModus = $('anzeigeModus').value
    optionen.minZeichen = Math.max(1, parseInt($('minZeichen').value, 10) || 3)
    optionen.debounceMs = Math.max(0, parseInt($('debounceMs').value, 10) || 180)
    await self.ffSpeichereOptionen(optionen)
  }

  for (const id of ['serverUrl', 'modus', 'anzeigeModus', 'minZeichen', 'debounceMs', 'profilStandard']) {
    $(id).addEventListener('change', speichern)
  }

  // Serverzustand + Profile laden.
  chrome.runtime.sendMessage({ typ: 'zustand', serverUrl: optionen.serverUrl }, (zustand) => {
    const el = $('status')
    if (zustand && zustand.online) {
      el.textContent = 'Server: verbunden'
      el.classList.add('online')
      profile = (zustand.capabilities && zustand.capabilities.profile) || profile
    } else {
      el.textContent = 'Server: offline'
      el.classList.add('offline')
    }
    fuelleProfile()
  })

  function fuelleProfile() {
    const sel = $('profilStandard')
    sel.innerHTML = ''
    for (const p of profile) {
      const opt = document.createElement('option')
      opt.value = p.id
      opt.textContent = p.name
      if (p.id === optionen.profilStandard) opt.selected = true
      sel.appendChild(opt)
    }
  }

  // Seiten-Tabelle.
  function zeichneSeiten() {
    const koerper = $('seitenTabelle').querySelector('tbody')
    koerper.innerHTML = ''
    const hosts = Object.keys(optionen.proSeite || {})
    $('keineSeiten').style.display = hosts.length ? 'none' : 'block'
    for (const host of hosts.sort()) {
      const s = self.ffSeite(optionen, host)
      const tr = document.createElement('tr')

      const tdHost = document.createElement('td')
      tdHost.textContent = host
      tr.appendChild(tdHost)

      tr.appendChild(schalterZelle(s.aktiv, (an) => setzeSeite(host, { aktiv: an })))

      const tdProfil = document.createElement('td')
      const sel = document.createElement('select')
      for (const p of profile) {
        const o = document.createElement('option')
        o.value = p.id
        o.textContent = p.name
        if (p.id === s.profil) o.selected = true
        sel.appendChild(o)
      }
      sel.addEventListener('change', () => setzeSeite(host, { profil: sel.value }))
      tdProfil.appendChild(sel)
      tr.appendChild(tdProfil)

      tr.appendChild(schalterZelle(s.lernen, (an) => setzeSeite(host, { lernen: an })))

      const tdWeg = document.createElement('td')
      const btn = document.createElement('button')
      btn.className = 'leer'
      btn.textContent = 'Entfernen'
      btn.addEventListener('click', async () => {
        delete optionen.proSeite[host]
        await self.ffSpeichereOptionen(optionen)
        zeichneSeiten()
      })
      tdWeg.appendChild(btn)
      tr.appendChild(tdWeg)

      koerper.appendChild(tr)
    }
  }

  function schalterZelle(an, beiWechsel) {
    const td = document.createElement('td')
    const cb = document.createElement('input')
    cb.type = 'checkbox'
    cb.checked = an
    cb.addEventListener('change', () => beiWechsel(cb.checked))
    td.appendChild(cb)
    return td
  }

  async function setzeSeite(host, teil) {
    const vorhanden = optionen.proSeite[host] || self.ffSeite(optionen, host)
    optionen.proSeite[host] = { ...vorhanden, ...teil }
    await self.ffSpeichereOptionen(optionen)
    zeichneSeiten()
  }

  $('hostSperren').addEventListener('click', async () => {
    const host = $('neuerHost').value.trim().toLowerCase()
    if (!host) return
    await setzeSeite(host, { aktiv: false })
    $('neuerHost').value = ''
  })

  zeichneSeiten()
})()
