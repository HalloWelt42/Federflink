/** Popup: globaler + pro-Seite-Schalter, Profilwahl, Serverzustand. */
;(async () => {
  const $ = (id) => document.getElementById(id)
  const optionen = await self.ffLadeOptionen()

  // Aktuellen Host der aktiven Seite bestimmen (activeTab).
  let host = ''
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true })
    if (tab && tab.url) host = new URL(tab.url).hostname
  } catch {
    /* keine Berechtigung fuer diese Seite */
  }
  $('host').textContent = host || 'dieser Seite'
  const seite = self.ffSeite(optionen, host)

  $('aktiv').checked = optionen.aktiv
  $('seiteAktiv').checked = seite.aktiv
  $('lernen').checked = seite.lernen

  async function speichern() {
    optionen.aktiv = $('aktiv').checked
    if (host) {
      optionen.proSeite[host] = {
        aktiv: $('seiteAktiv').checked,
        profil: $('profil').value || optionen.profilStandard,
        lernen: $('lernen').checked,
      }
    }
    await self.ffSpeichereOptionen(optionen)
  }

  $('aktiv').addEventListener('change', speichern)
  $('seiteAktiv').addEventListener('change', speichern)
  $('lernen').addEventListener('change', speichern)
  $('profil').addEventListener('change', speichern)
  $('optionen').addEventListener('click', (e) => {
    e.preventDefault()
    chrome.runtime.openOptionsPage()
  })

  // Serverzustand + Profile laden.
  chrome.runtime.sendMessage({ typ: 'zustand', serverUrl: optionen.serverUrl }, (zustand) => {
    const el = $('status')
    if (zustand && zustand.online) {
      el.textContent = 'verbunden'
      el.classList.add('online')
      const profile = (zustand.capabilities && zustand.capabilities.profile) || []
      fuelleProfile(profile, seite.profil)
    } else {
      el.textContent = 'offline'
      el.classList.add('offline')
      fuelleProfile([{ id: optionen.profilStandard, name: optionen.profilStandard }], seite.profil)
    }
  })

  function fuelleProfile(profile, gewaehlt) {
    const sel = $('profil')
    sel.innerHTML = ''
    for (const p of profile) {
      const opt = document.createElement('option')
      opt.value = p.id
      opt.textContent = p.name
      if (p.id === gewaehlt) opt.selected = true
      sel.appendChild(opt)
    }
  }
})()
