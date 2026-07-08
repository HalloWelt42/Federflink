<script lang="ts">
  import { onMount } from 'svelte'

  import { ladeCapabilities } from '../api/system'
  import { entferneWort, fuegeWortHinzu, ladeWoerterbuch } from '../api/woerterbuch'
  import type { CapabilitiesAntwort, WortEintrag } from '../api/typen'

  let caps = $state<CapabilitiesAntwort | null>(null)
  let profil = $state('standard')
  let woerter = $state<WortEintrag[]>([])
  let anzahl = $state(0)
  let neuesWort = $state('')
  let fehler = $state('')
  let laedt = $state(false)

  async function laden() {
    laedt = true
    fehler = ''
    try {
      const antwort = await ladeWoerterbuch(profil)
      woerter = antwort.woerter
      anzahl = antwort.anzahl
    } catch (e) {
      fehler = e instanceof Error ? e.message : String(e)
    } finally {
      laedt = false
    }
  }

  async function hinzufuegen() {
    const wort = neuesWort.trim()
    if (!wort) return
    try {
      await fuegeWortHinzu(wort, profil)
      neuesWort = ''
      await laden()
    } catch (e) {
      fehler = e instanceof Error ? e.message : String(e)
    }
  }

  async function entfernen(wort: string) {
    try {
      await entferneWort(wort, profil)
      await laden()
    } catch (e) {
      fehler = e instanceof Error ? e.message : String(e)
    }
  }

  onMount(async () => {
    caps = await ladeCapabilities().catch(() => null)
    await laden()
  })
</script>

<div class="karte">
  <div class="karte-kopf">
    <i class="fa-solid fa-book"></i> Persönliches Wörterbuch
    <span class="abzeichen" style="margin-left:auto">{anzahl} Wörter gesamt</span>
  </div>
  <div class="karte-inhalt">
    <div class="werkzeugzeile">
      <label class="feld-zeile">
        <span class="beschriftung">Profil</span>
        <select class="feld" style="width:auto" bind:value={profil} onchange={laden}>
          {#each caps?.profile ?? [{ id: 'standard', name: 'Standard' }] as p (p.id)}
            <option value={p.id}>{p.name}</option>
          {/each}
        </select>
      </label>
      <span style="flex:1"></span>
      <input
        class="feld"
        style="max-width:220px"
        placeholder="Wort hinzufügen ..."
        bind:value={neuesWort}
        onkeydown={(e) => e.key === 'Enter' && hinzufuegen()}
      />
      <button class="knopf primaer" onclick={hinzufuegen} disabled={!neuesWort.trim()}>
        <i class="fa-solid fa-plus"></i> Hinzufügen
      </button>
    </div>

    {#if fehler}
      <p class="abzeichen fehler">{fehler}</p>
    {/if}

    {#if laedt}
      <p class="hinweis-text"><i class="fa-solid fa-spinner spinner"></i> Lädt ...</p>
    {:else if woerter.length === 0}
      <div class="leer-zustand" style="padding: var(--a4)">
        <i class="fa-solid fa-book-open"></i>
        <strong>Noch keine Wörter</strong>
        <span class="hinweis-text">Füge eigene Wörter hinzu oder lerne sie in der Spielwiese.</span>
      </div>
    {:else}
      <table class="tabelle">
        <thead>
          <tr><th>Wort</th><th>Profil</th><th style="text-align:right">Häufigkeit</th><th>Quelle</th><th></th></tr>
        </thead>
        <tbody>
          {#each woerter as w (w.wort + w.profil_id)}
            <tr>
              <td class="mono">{w.wort}</td>
              <td>{w.profil_id}</td>
              <td style="text-align:right">{w.haeufigkeit}</td>
              <td>{w.quelle}</td>
              <td style="text-align:right">
                <button class="icon-knopf" title="Entfernen" aria-label="Entfernen" onclick={() => entfernen(w.wort)}>
                  <i class="fa-solid fa-trash-can"></i>
                </button>
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    {/if}
  </div>
</div>
