<script lang="ts">
  import { onMount } from 'svelte'

  import { ladeCapabilities } from '../api/system'
  import { korrigiere, pruefe, satzVorschlaege } from '../api/pruefung'
  import { fuegeWortHinzu } from '../api/woerterbuch'
  import type { Befund, CapabilitiesAntwort, KorrekturAntwort } from '../api/typen'
  import { wortDiff } from '../textDiff'

  const BEISPIEL =
    'Ich glab das Ergibnis stimt nich ganz. Bitte pruef die Strasse nochmal, den der Fehlar ist wichtig.'

  let text = $state(BEISPIEL)
  let caps = $state<CapabilitiesAntwort | null>(null)
  let profil = $state('standard')
  let aktiveEngines = $state<string[]>([])

  let befunde = $state<Befund[]>([])
  let basisText = $state('')
  let geprueft = $state(false)
  let pruefEngines = $state<string[]>([])
  let pruefDauer = $state(0)
  let pruefLaeuft = $state(false)

  let korrektur = $state<KorrekturAntwort | null>(null)
  let korrLaeuft = $state(false)
  let fehler = $state('')

  let feldEl: HTMLTextAreaElement | undefined
  let satzListe = $state<string[]>([])
  let satzOriginal = $state('')
  let satzGeprueft = $state(false)
  let satzLaeuft = $state(false)
  let satzSpan: { start: number; ende: number } | null = null

  const artLabel: Record<string, string> = {
    rechtschreibung: 'Rechtschreibung',
    grammatik: 'Grammatik',
    zeichensetzung: 'Zeichensetzung',
    stil: 'Stil',
    tippfehler: 'Tippfehler',
  }

  onMount(async () => {
    try {
      caps = await ladeCapabilities()
      aktiveEngines = caps.pruef_engines.filter((e) => e.aktiv && e.standard_an).map((e) => e.id)
    } catch (e) {
      fehler = e instanceof Error ? e.message : String(e)
    }
  })

  function engineUmschalten(id: string) {
    aktiveEngines = aktiveEngines.includes(id)
      ? aktiveEngines.filter((x) => x !== id)
      : [...aktiveEngines, id]
  }

  function wortVon(b: Befund): string {
    return basisText.slice(b.offset, b.offset + b.laenge)
  }

  async function pruefen() {
    fehler = ''
    pruefLaeuft = true
    korrektur = null
    try {
      basisText = text
      const antwort = await pruefe(text, profil, aktiveEngines.length ? aktiveEngines : undefined)
      befunde = antwort.befunde
      pruefEngines = antwort.engines
      pruefDauer = antwort.dauer_ms
      geprueft = true
    } catch (e) {
      fehler = e instanceof Error ? e.message : String(e)
    } finally {
      pruefLaeuft = false
    }
  }

  async function vorschlagAnwenden(b: Befund, vorschlag: string) {
    // Gegen den geprüften Stand anwenden, dann neu prüfen (Offsets bleiben gültig).
    text = basisText.slice(0, b.offset) + vorschlag + basisText.slice(b.offset + b.laenge)
    await pruefen()
  }

  async function insWoerterbuch(b: Befund) {
    try {
      await fuegeWortHinzu(wortVon(b), profil)
      await pruefen()
    } catch (e) {
      fehler = e instanceof Error ? e.message : String(e)
    }
  }

  async function verbessern() {
    fehler = ''
    korrLaeuft = true
    korrektur = null
    try {
      korrektur = await korrigiere(text)
    } catch (e) {
      fehler = e instanceof Error ? e.message : String(e)
    } finally {
      korrLaeuft = false
    }
  }

  function korrekturUebernehmen() {
    if (korrektur) {
      text = korrektur.korrigiert
      korrektur = null
      befunde = []
      geprueft = false
    }
  }

  // Satz um den Cursor bestimmen (nur EIN Satz - das haelt die Anfrage schnell).
  function satzSpanne(t: string, pos: number): { start: number; ende: number } {
    const trenner = '.!?\n'
    let start = 0
    for (let i = Math.min(pos, t.length) - 1; i >= 0; i--) {
      if (trenner.includes(t[i])) {
        start = i + 1
        break
      }
    }
    let ende = t.length
    for (let i = Math.max(0, pos); i < t.length; i++) {
      if (trenner.includes(t[i])) {
        ende = i + 1
        break
      }
    }
    const roh = t.slice(start, ende)
    const vorn = roh.length - roh.trimStart().length
    const hinten = roh.length - roh.trimEnd().length
    return { start: start + vorn, ende: ende - hinten }
  }

  async function satzVerbessern() {
    fehler = ''
    satzListe = []
    satzGeprueft = false
    const pos = feldEl?.selectionStart ?? text.length
    const span = satzSpanne(text, pos)
    const satz = text.slice(span.start, span.ende)
    if (satz.trim().length < 3) {
      fehler = 'Kein Satz am Cursor gefunden.'
      return
    }
    satzSpan = span
    satzOriginal = satz
    satzLaeuft = true
    try {
      const antwort = await satzVorschlaege(satz, profil)
      satzListe = antwort.vorschlaege
      satzGeprueft = true
    } catch (e) {
      fehler = e instanceof Error ? e.message : String(e)
    } finally {
      satzLaeuft = false
    }
  }

  function satzAnwenden(variante: string) {
    if (!satzSpan) return
    text = text.slice(0, satzSpan.start) + variante + text.slice(satzSpan.ende)
    satzListe = []
    satzGeprueft = false
    satzSpan = null
  }

  function beiEingabe() {
    // Ergebnisse verwerfen, sobald der Nutzer selbst tippt (nicht bei Programmänderung).
    befunde = []
    geprueft = false
    korrektur = null
    satzListe = []
    satzGeprueft = false
  }

  const llmErreichbar = $derived(caps?.llm?.erreichbar ?? false)
  const diffTeile = $derived(korrektur ? wortDiff(korrektur.original, korrektur.korrigiert) : [])
</script>

<div class="karte">
  <div class="karte-kopf"><i class="fa-solid fa-pen-nib"></i> Spielwiese</div>
  <div class="karte-inhalt">
    <div class="werkzeugzeile">
      <label class="feld-zeile">
        <span class="beschriftung">Profil</span>
        <select class="feld" style="width:auto" bind:value={profil}>
          {#each caps?.profile ?? [] as p (p.id)}
            <option value={p.id}>{p.name}</option>
          {/each}
        </select>
      </label>

      <span class="trenner"></span>

      {#each caps?.pruef_engines ?? [] as e (e.id)}
        <button
          class="chip"
          class:an={aktiveEngines.includes(e.id)}
          class:deaktiviert={!e.aktiv}
          disabled={!e.aktiv}
          title={e.aktiv ? e.name : `${e.name} nicht verfügbar`}
          onclick={() => engineUmschalten(e.id)}
        >
          <i class="fa-solid {aktiveEngines.includes(e.id) ? 'fa-check' : 'fa-xmark'}"></i>
          {e.name}
        </button>
      {/each}
    </div>

    <textarea
      bind:this={feldEl}
      class="feld"
      rows="5"
      placeholder="Text zum Prüfen oder Verbessern ..."
      bind:value={text}
      oninput={beiEingabe}
    ></textarea>

    <div class="werkzeugzeile">
      <button class="knopf primaer" onclick={pruefen} disabled={pruefLaeuft || !text.trim()}>
        {#if pruefLaeuft}<i class="fa-solid fa-spinner spinner"></i>{:else}<i class="fa-solid fa-spell-check"></i>{/if}
        Rechtschreibung prüfen
      </button>
      <button
        class="knopf"
        onclick={verbessern}
        disabled={korrLaeuft || !text.trim() || !llmErreichbar}
        title={llmErreichbar ? 'Ganzsatz-Korrektur per Sprachmodell' : 'Kein Sprachmodell erreichbar'}
      >
        {#if korrLaeuft}<i class="fa-solid fa-spinner spinner"></i>{:else}<i class="fa-solid fa-wand-magic-sparkles"></i>{/if}
        Text verbessern (KI)
      </button>
      <button
        class="knopf"
        onclick={satzVerbessern}
        disabled={satzLaeuft || !text.trim() || !llmErreichbar}
        title={llmErreichbar ? 'Den Satz am Cursor auf Sinn und Wortwahl verbessern (3 Vorschläge)' : 'Kein Sprachmodell erreichbar'}
      >
        {#if satzLaeuft}<i class="fa-solid fa-spinner spinner"></i>{:else}<i class="fa-solid fa-comment-dots"></i>{/if}
        Satz verbessern
      </button>
      {#if geprueft && !pruefLaeuft}
        <span class="hinweis-text">
          {befunde.length} Fund(e) - Engines: {pruefEngines.join(', ') || 'keine'} - {pruefDauer} ms
        </span>
      {/if}
    </div>

    {#if fehler}
      <p class="abzeichen fehler">{fehler}</p>
    {/if}
  </div>
</div>

{#if korrektur}
  <div class="karte">
    <div class="karte-kopf"><i class="fa-solid fa-wand-magic-sparkles"></i> Korrektur-Vorschau (nichts wird automatisch übernommen)</div>
    <div class="karte-inhalt">
      {#if korrektur.veraendert}
        <div class="diff-anzeige">
          {#each diffTeile as t}<span class="d-{t.typ}">{t.text}</span>{/each}
        </div>
        <div class="werkzeugzeile">
          <button class="knopf primaer" onclick={korrekturUebernehmen}><i class="fa-solid fa-check"></i> Korrigierten Text übernehmen</button>
          <button class="knopf" onclick={() => (korrektur = null)}><i class="fa-solid fa-xmark"></i> Verwerfen</button>
        </div>
      {:else}
        <p class="hinweis-text"><i class="fa-solid fa-circle-check"></i> Das Sprachmodell hat nichts zu korrigieren gefunden (oder es war nicht erreichbar - dann bleibt der Text unverändert).</p>
      {/if}
    </div>
  </div>
{/if}

{#if satzGeprueft}
  <div class="karte">
    <div class="karte-kopf"><i class="fa-solid fa-comment-dots"></i> Satz-Vorschläge (nur der Satz am Cursor)</div>
    <div class="karte-inhalt">
      <p class="hinweis-text" style="margin-bottom: var(--a2)">Original: <span class="mono">{satzOriginal}</span></p>
      {#if satzListe.length === 0}
        <div class="leer-zustand" style="padding: var(--a4)">
          <i class="fa-solid fa-circle-check" style="color: var(--zustand-erfolg)"></i>
          <strong>Keine Verbesserung nötig</strong>
          <span class="hinweis-text">Der Satz wirkt sinnvoll und stimmig.</span>
        </div>
      {:else}
        {#each satzListe as v, i (i)}
          <button class="satz-vorschlag" onclick={() => satzAnwenden(v)} title="Diesen Satz übernehmen">
            <i class="fa-solid fa-arrow-right"></i> {v}
          </button>
        {/each}
      {/if}
    </div>
  </div>
{/if}

{#if geprueft && !pruefLaeuft}
  <div class="karte">
    <div class="karte-kopf"><i class="fa-solid fa-list-check"></i> Funde</div>
    <div class="karte-inhalt">
      {#if befunde.length === 0}
        <div class="leer-zustand" style="padding: var(--a4)">
          <i class="fa-solid fa-circle-check" style="color: var(--zustand-erfolg)"></i>
          <strong>Keine Funde</strong>
          <span class="hinweis-text">Der Text ist rechtschreiblich sauber.</span>
        </div>
      {:else}
        {#each befunde as b, i (i)}
          <div class="befund-zeile">
            <span class="abzeichen {b.art === 'rechtschreibung' ? 'fehler' : 'warnung'}">{artLabel[b.art] ?? b.art}</span>
            <span class="befund-wort mono">{wortVon(b)}</span>
            <span class="vorschlag-liste">
              {#each b.vorschlaege as v}
                <button class="chip anwendbar" onclick={() => vorschlagAnwenden(b, v)} title="Übernehmen">{v}</button>
              {/each}
              {#if b.vorschlaege.length === 0}
                <span class="hinweis-text">keine Vorschläge</span>
              {/if}
            </span>
            {#if b.art === 'rechtschreibung'}
              <button class="icon-knopf" title="Ins persönliche Wörterbuch" aria-label="Ins Wörterbuch" onclick={() => insWoerterbuch(b)}>
                <i class="fa-solid fa-book-medical"></i>
              </button>
            {/if}
          </div>
        {/each}
      {/if}
    </div>
  </div>
{/if}

<style>
  .werkzeugzeile {
    display: flex;
    align-items: center;
    gap: var(--a2);
    flex-wrap: wrap;
    margin-bottom: var(--a3);
  }
  textarea.feld {
    margin-bottom: var(--a3);
    font-size: 0.95rem;
  }
  .trenner {
    width: 1px;
    align-self: stretch;
    background: var(--rand-1);
    margin: 0 var(--a1);
  }
  .chip {
    display: inline-flex;
    align-items: center;
    gap: var(--a1);
    height: 26px;
    padding: 0 var(--a2);
    border: 1px solid var(--rand-2);
    border-radius: var(--radius-knopf);
    background: var(--flaeche-panel-2);
    color: var(--text-2);
    font-size: 0.82rem;
    cursor: pointer;
  }
  .chip.an {
    background: var(--akzent-weich);
    color: var(--text-1);
    border-color: var(--akzent);
  }
  .chip.deaktiviert {
    opacity: 0.5;
    cursor: not-allowed;
  }
  .chip.anwendbar {
    background: var(--flaeche-eingabe);
    color: var(--akzent);
    font-family: var(--schrift-mono);
  }
  .chip.anwendbar:hover {
    background: var(--akzent);
    color: var(--auf-akzent);
  }
  .befund-zeile {
    display: flex;
    align-items: center;
    gap: var(--a3);
    padding: var(--a2) 0;
    border-bottom: 1px solid var(--rand-1);
  }
  .befund-wort {
    min-width: 120px;
    color: var(--zustand-fehler);
    font-weight: 600;
  }
  .vorschlag-liste {
    display: flex;
    gap: var(--a1);
    flex-wrap: wrap;
    flex: 1;
  }
  .diff-anzeige {
    font-size: 0.98rem;
    line-height: 1.7;
    background: var(--flaeche-eingabe);
    border: 1px solid var(--rand-1);
    padding: var(--a3);
    margin-bottom: var(--a3);
    white-space: pre-wrap;
  }
  .d-gleich {
    color: var(--text-1);
  }
  .d-hinzu {
    background: var(--diff-hinzu);
    color: var(--zustand-erfolg);
    border-radius: 2px;
  }
  .d-weg {
    background: var(--diff-weg);
    color: var(--zustand-fehler);
    text-decoration: line-through;
    border-radius: 2px;
  }
  .satz-vorschlag {
    display: block;
    width: 100%;
    text-align: left;
    padding: var(--a2) var(--a3);
    margin-bottom: var(--a2);
    border: 1px solid var(--rand-2);
    border-radius: var(--radius-knopf);
    background: var(--flaeche-eingabe);
    color: var(--text-1);
    font-family: var(--schrift-anzeige);
    font-size: 0.95rem;
    cursor: pointer;
  }
  .satz-vorschlag i {
    color: var(--akzent);
    margin-right: var(--a1);
  }
  .satz-vorschlag:hover {
    background: var(--akzent-weich);
    border-color: var(--akzent);
  }
</style>
