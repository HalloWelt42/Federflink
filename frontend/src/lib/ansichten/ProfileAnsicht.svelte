<script lang="ts">
  import { onMount } from 'svelte'

  import { entferneProfil, ladeProfile, legeProfilAn } from '../api/profile'
  import type { Profil } from '../api/typen'

  let profile = $state<Profil[]>([])
  let fehler = $state('')
  let laedt = $state(true)

  let neuId = $state('')
  let neuName = $state('')
  let neuStil = $state('')
  let neuHosts = $state('')

  async function laden() {
    laedt = true
    fehler = ''
    try {
      profile = await ladeProfile()
    } catch (e) {
      fehler = e instanceof Error ? e.message : String(e)
    } finally {
      laedt = false
    }
  }

  async function anlegen() {
    const id = neuId.trim().toLowerCase().replace(/\s+/g, '-')
    if (!id || !neuName.trim()) return
    try {
      await legeProfilAn({
        id,
        name: neuName.trim(),
        stil_prompt: neuStil.trim(),
        host_muster: neuHosts
          .split(',')
          .map((h) => h.trim())
          .filter(Boolean),
      })
      neuId = ''
      neuName = ''
      neuStil = ''
      neuHosts = ''
      await laden()
    } catch (e) {
      fehler = e instanceof Error ? e.message : String(e)
    }
  }

  async function entfernen(id: string) {
    try {
      await entferneProfil(id)
      await laden()
    } catch (e) {
      fehler = e instanceof Error ? e.message : String(e)
    }
  }

  onMount(laden)
</script>

<div class="karte">
  <div class="karte-kopf"><i class="fa-solid fa-user-pen"></i> Schreibprofile</div>
  <div class="karte-inhalt">
    <p class="hinweis-text" style="margin-bottom: var(--a3)">
      Ein Profil bündelt Ton/Stil, ein eigenes Wörterbuch und einen eigenen Umfeld-Kontext.
      Host-Muster (z. B. <code>*.example.org</code>) ordnen Seiten automatisch einem Profil zu.
    </p>

    {#if fehler}<p class="abzeichen fehler">{fehler}</p>{/if}

    {#if laedt}
      <p class="hinweis-text"><i class="fa-solid fa-spinner spinner"></i> Lädt ...</p>
    {:else}
      <table class="tabelle">
        <thead>
          <tr><th>Profil</th><th>Stilhinweis</th><th>Host-Muster</th><th></th></tr>
        </thead>
        <tbody>
          {#each profile as p (p.id)}
            <tr>
              <td>
                <strong>{p.name}</strong> <span class="mono" style="color:var(--text-3)">{p.id}</span>
                {#if p.eingebaut}<span class="abzeichen info">eingebaut</span>{/if}
              </td>
              <td style="max-width:280px; color:var(--text-2)">{p.stil_prompt || '-'}</td>
              <td class="mono" style="font-size:0.78rem">{p.host_muster.join(', ') || '-'}</td>
              <td style="text-align:right">
                {#if !p.eingebaut}
                  <button class="icon-knopf" title="Entfernen" aria-label="Entfernen" onclick={() => entfernen(p.id)}>
                    <i class="fa-solid fa-trash-can"></i>
                  </button>
                {/if}
              </td>
            </tr>
          {/each}
        </tbody>
      </table>
    {/if}
  </div>
</div>

<div class="karte">
  <div class="karte-kopf"><i class="fa-solid fa-plus"></i> Neues Profil</div>
  <div class="karte-inhalt">
    <div class="raster">
      <label class="feld-zeile spalte"><span class="beschriftung">Kurzname (Id)</span><input class="feld" bind:value={neuId} placeholder="z. B. notizen" /></label>
      <label class="feld-zeile spalte"><span class="beschriftung">Anzeigename</span><input class="feld" bind:value={neuName} placeholder="z. B. Notizen" /></label>
    </div>
    <label class="feld-zeile spalte" style="margin-top: var(--a3)">
      <span class="beschriftung">Stilhinweis (für die KI-Ergänzung)</span>
      <input class="feld" bind:value={neuStil} placeholder="z. B. knapp und sachlich" />
    </label>
    <label class="feld-zeile spalte" style="margin-top: var(--a3)">
      <span class="beschriftung">Host-Muster (kommagetrennt, optional)</span>
      <input class="feld" bind:value={neuHosts} placeholder="z. B. *.example.org, notizen.local" />
    </label>
    <div style="margin-top: var(--a3)">
      <button class="knopf primaer" onclick={anlegen} disabled={!neuId.trim() || !neuName.trim()}>
        <i class="fa-solid fa-check"></i> Profil anlegen
      </button>
    </div>
  </div>
</div>

<style>
  .raster {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: var(--a3);
  }
  .spalte {
    flex-direction: column;
    align-items: stretch;
    gap: 4px;
  }
</style>
