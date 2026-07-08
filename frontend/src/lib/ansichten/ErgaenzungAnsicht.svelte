<script lang="ts">
  import { onMount, tick } from 'svelte'

  import { ergaenzeStream, lerne } from '../api/ergaenzung'
  import { ladeCapabilities } from '../api/system'
  import type { CapabilitiesAntwort, ErgaenzungsModus, LernStatus, Vorschlag } from '../api/typen'
  import { requestJson } from '../api/http'

  const START_TEXT = 'Sehr geehrte Damen und Herren, '
  let text = $state(START_TEXT)
  let caret = $state(START_TEXT.length)
  let profil = $state('standard')
  let modus = $state<ErgaenzungsModus>('phrase')
  let caps = $state<CapabilitiesAntwort | null>(null)

  let vorschlag = $state<Vorschlag | null>(null)
  let alternativen = $state<Vorschlag[]>([])
  let fehler = $state('')
  let lernStatus = $state<LernStatus | null>(null)

  let feldEl: HTMLTextAreaElement | undefined
  let entprellung: ReturnType<typeof setTimeout> | undefined
  let laufend: AbortController | undefined

  const textVor = $derived(text.slice(0, caret))
  const textNach = $derived(text.slice(caret))
  const amEnde = $derived(textNach.length === 0)
  const geistText = $derived(vorschlag?.text ?? '')

  async function ladeStatus() {
    lernStatus = await requestJson<LernStatus>('/api/status').catch(() => null)
  }

  onMount(async () => {
    caps = await ladeCapabilities().catch(() => null)
    await ladeStatus()
  })

  function planeAnforderung() {
    clearTimeout(entprellung)
    const ms = caps?.grenzen.debounce_ms ?? 150
    entprellung = setTimeout(anfordern, ms)
  }

  function anfordern() {
    laufend?.abort()
    const controller = new AbortController()
    laufend = controller
    fehler = ''
    void ergaenzeStream(
      {
        text_vor: textVor,
        text_nach: textNach,
        modus,
        profil_id: profil,
        max_vorschlaege: caps?.grenzen.max_vorschlaege ?? 3,
        seite: { host: 'spielwiese', feld_art: 'textarea', sprach_hinweis: 'de' },
      },
      {
        beiInstant: (vs) => {
          vorschlag = vs[0] ?? null
          alternativen = vs.slice(1)
        },
        beiUpgrade: (vs) => {
          // Besseren LLM-Vorschlag voranstellen, den Instant-Vorschlag als Alternative behalten.
          if (vs[0]) {
            if (vorschlag) alternativen = [vorschlag, ...alternativen].slice(0, 3)
            vorschlag = vs[0]
          }
        },
        beiFehler: (e) => {
          fehler = e instanceof Error ? e.message : String(e)
        },
      },
      controller.signal,
    )
  }

  function verwerfen() {
    vorschlag = null
    alternativen = []
  }

  async function uebernehmen(v: Vorschlag | null) {
    if (!v) return
    const vor = textVor
    const neu = vor + v.text + textNach
    const neuerCaret = (vor + v.text).length
    // Lernen im Hintergrund (Kontext wird mitgeschickt - hier ist es die Spielwiese).
    void lerne({
      uebernommen_text: v.text,
      uebernommen_engine: v.engine,
      text_vor: vor,
      profil_id: profil,
      seite: { host: 'spielwiese', feld_art: 'textarea', sprach_hinweis: 'de' },
    }).then(ladeStatus)

    text = neu
    caret = neuerCaret
    vorschlag = null
    alternativen = []
    await tick()
    if (feldEl) {
      feldEl.focus()
      feldEl.setSelectionRange(neuerCaret, neuerCaret)
    }
    planeAnforderung()
  }

  function beiTaste(e: KeyboardEvent) {
    if (e.key === 'Tab' && vorschlag && amEnde) {
      e.preventDefault()
      void uebernehmen(vorschlag)
    } else if (e.key === 'Escape' && vorschlag) {
      e.preventDefault()
      verwerfen()
    }
  }

  function synchronisiereCaret() {
    if (feldEl) caret = feldEl.selectionStart
  }

  function beiEingabe() {
    if (feldEl) caret = feldEl.selectionStart
    vorschlag = null
    planeAnforderung()
  }

  function spiegelScroll() {
    const spiegel = feldEl?.previousElementSibling as HTMLElement | null
    if (spiegel && feldEl) spiegel.scrollTop = feldEl.scrollTop
  }
</script>

<div class="karte">
  <div class="karte-kopf"><i class="fa-solid fa-wand-sparkles"></i> Ergänzung ausprobieren</div>
  <div class="karte-inhalt">
    <div class="leiste">
      <label class="feld-zeile">
        <span class="beschriftung">Profil</span>
        <select class="feld" style="width:auto" bind:value={profil}>
          {#each caps?.profile ?? [] as p (p.id)}<option value={p.id}>{p.name}</option>{/each}
        </select>
      </label>
      <label class="feld-zeile">
        <span class="beschriftung">Modus</span>
        <select class="feld" style="width:auto" bind:value={modus} onchange={anfordern}>
          <option value="wort">Wort</option>
          <option value="phrase">Phrase</option>
          <option value="satz">Satz</option>
        </select>
      </label>
      <span style="flex:1"></span>
      {#if lernStatus}
        <span class="abzeichen"><i class="fa-solid fa-graduation-cap"></i> {lernStatus.woerter} Wörter - {lernStatus.ngramme} N-Gramme</span>
      {/if}
    </div>

    <div class="editor-huelle">
      <div class="geist-spiegel" aria-hidden="true">
        <span class="unsichtbar">{textVor}</span>{#if vorschlag && amEnde}<span class="geist">{geistText}</span>{/if}<span class="unsichtbar">{textNach}</span>
      </div>
      <textarea
        bind:this={feldEl}
        class="geist-eingabe"
        rows="4"
        bind:value={text}
        oninput={beiEingabe}
        onkeydown={beiTaste}
        onkeyup={synchronisiereCaret}
        onclick={synchronisiereCaret}
        onscroll={spiegelScroll}
        placeholder="Tippe los ... Vorschlag mit Tab übernehmen."
      ></textarea>
    </div>

    <div class="leiste">
      {#if vorschlag}
        <button class="knopf primaer" onclick={() => uebernehmen(vorschlag)}>
          <i class="fa-solid fa-check"></i> Übernehmen (Tab)
        </button>
        <span class="hinweis-text">Vorschlag von <strong>{vorschlag.engine}</strong> (Score {vorschlag.score.toFixed(2)}){amEnde ? '' : ' - Cursor nicht am Ende, daher nur unten angezeigt'}</span>
      {:else}
        <span class="hinweis-text">Noch kein Vorschlag - tippe weiter. N-Gramme lernst du durch Übernehmen dazu.</span>
      {/if}
    </div>

    {#if alternativen.length}
      <div class="leiste">
        <span class="beschriftung">Alternativen:</span>
        {#each alternativen as v (v.id)}
          <button class="chip anwendbar" onclick={() => uebernehmen(v)}>{v.text.trim() || '(leer)'}</button>
        {/each}
      </div>
    {/if}

    {#if fehler}<p class="abzeichen fehler">{fehler}</p>{/if}
  </div>
</div>

<style>
  .leiste {
    display: flex;
    align-items: center;
    gap: var(--a2);
    flex-wrap: wrap;
    margin-bottom: var(--a3);
  }
  .editor-huelle {
    position: relative;
    margin-bottom: var(--a3);
  }
  .geist-spiegel,
  .geist-eingabe {
    font-family: var(--schrift-anzeige);
    font-size: 0.98rem;
    line-height: 1.6;
    padding: var(--a2);
    border: 1px solid var(--rand-2);
    border-radius: var(--radius-eingabe);
    box-sizing: border-box;
    width: 100%;
    white-space: pre-wrap;
    overflow-wrap: break-word;
    word-break: normal;
  }
  .geist-spiegel {
    position: absolute;
    inset: 0;
    background: var(--flaeche-eingabe);
    color: transparent;
    overflow: hidden;
    pointer-events: none;
    z-index: 0;
  }
  .geist-spiegel .unsichtbar {
    color: transparent;
  }
  .geist-spiegel .geist {
    color: var(--geist);
  }
  .geist-eingabe {
    position: relative;
    z-index: 1;
    background: transparent;
    color: var(--text-1);
    resize: vertical;
    min-height: 96px;
  }
  .geist-eingabe:focus {
    outline: 2px solid var(--akzent);
    outline-offset: -1px;
  }
  .chip.anwendbar {
    display: inline-flex;
    align-items: center;
    height: 26px;
    padding: 0 var(--a2);
    border: 1px solid var(--rand-2);
    border-radius: var(--radius-knopf);
    background: var(--flaeche-eingabe);
    color: var(--akzent);
    font-family: var(--schrift-mono);
    font-size: 0.82rem;
    cursor: pointer;
  }
  .chip.anwendbar:hover {
    background: var(--akzent);
    color: var(--auf-akzent);
  }
</style>
