/**
 * MAIN-World-Helfer: fuegt beim Uebernehmen Text robust in Framework-Felder
 * (React/Vue u. a.) ein, indem der native value-Setter des Prototyps aufgerufen
 * und ein echtes input-Event ausgeloest wird. Laeuft in der Seitenwelt, weil das
 * isolierte Content-Skript den Wert-Tracker mancher Frameworks nicht ausloest.
 *
 * Nachrichten kommen per window.postMessage mit Namensraum '__FEDERFLINK__'.
 */
;(() => {
  const NS = '__FEDERFLINK__'
  window.addEventListener('message', (ereignis) => {
    if (ereignis.source !== window) return
    const daten = ereignis.data
    if (!daten || daten.ns !== NS || daten.typ !== 'einfuegen') return

    const el = document.activeElement
    if (!el) return
    const wert = String(daten.wert ?? '')
    const cursor = Number(daten.cursor ?? wert.length)

    if (el.tagName === 'INPUT' || el.tagName === 'TEXTAREA') {
      const proto =
        el.tagName === 'TEXTAREA' ? window.HTMLTextAreaElement.prototype : window.HTMLInputElement.prototype
      const setter = Object.getOwnPropertyDescriptor(proto, 'value')?.set
      if (setter) {
        setter.call(el, wert)
      } else {
        el.value = wert
      }
      el.dispatchEvent(new Event('input', { bubbles: true }))
      try {
        el.setSelectionRange(cursor, cursor)
      } catch {
        /* manche Eingabetypen erlauben keine Selektion */
      }
    }
  })
})()
