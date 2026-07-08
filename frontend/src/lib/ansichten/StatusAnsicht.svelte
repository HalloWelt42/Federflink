<script lang="ts">
  import { onMount } from 'svelte'

  import { ladeCapabilities } from '../api/system'
  import type { CapabilitiesAntwort } from '../api/typen'

  let caps = $state<CapabilitiesAntwort | null>(null)
  let fehler = $state('')
  let laedt = $state(true)

  async function laden() {
    laedt = true
    fehler = ''
    try {
      caps = await ladeCapabilities()
    } catch (e) {
      fehler = e instanceof Error ? e.message : String(e)
    } finally {
      laedt = false
    }
  }

  onMount(laden)
</script>

<div class="karte">
  <div class="karte-kopf">
    <i class="fa-solid fa-gauge-high"></i>
    Serverzustand
    <button class="icon-knopf" style="margin-left:auto" title="Neu laden" aria-label="Neu laden" onclick={laden}>
      <i class="fa-solid fa-rotate"></i>
    </button>
  </div>
  <div class="karte-inhalt">
    {#if laedt}
      <p class="hinweis-text"><i class="fa-solid fa-spinner spinner"></i> Lade Capabilities ...</p>
    {:else if fehler}
      <p class="abzeichen fehler">{fehler}</p>
    {:else if caps}
      <div class="kennzahl-raster">
        <div class="kennzahl">
          <div class="kz-wert">{caps.version}</div>
          <div class="kz-name">Version</div>
        </div>
        <div class="kennzahl">
          <div class="kz-wert">{caps.pruef_engines.length}</div>
          <div class="kz-name">Pruef-Engines</div>
        </div>
        <div class="kennzahl">
          <div class="kz-wert">{caps.ergaenzungs_engines.length}</div>
          <div class="kz-name">Ergaenzungs-Engines</div>
        </div>
        <div class="kennzahl">
          <div class="kz-wert">{caps.profile.length}</div>
          <div class="kz-name">Profile</div>
        </div>
      </div>

      <div style="margin-top: var(--a4)">
        <h3 style="margin:0 0 var(--a2); font-size:0.95rem">Engines</h3>
        {#if caps.pruef_engines.length === 0 && caps.ergaenzungs_engines.length === 0}
          <p class="hinweis-text">
            Noch keine Engines registriert. Rechtschreibung und Ergaenzung folgen in den
            naechsten Ausbaustufen.
          </p>
        {:else}
          <table class="tabelle">
            <thead>
              <tr><th>Engine</th><th>Art</th><th>Aktiv</th><th>Standard an</th></tr>
            </thead>
            <tbody>
              {#each caps.pruef_engines as e (e.id)}
                <tr>
                  <td>{e.name}</td>
                  <td>Pruefung</td>
                  <td><span class="abzeichen {e.aktiv ? 'gut' : 'fehler'}">{e.aktiv ? 'ja' : 'nein'}</span></td>
                  <td>{e.standard_an ? 'ja' : 'nein'}</td>
                </tr>
              {/each}
              {#each caps.ergaenzungs_engines as e (e.id)}
                <tr>
                  <td>{e.name}</td>
                  <td>Ergaenzung</td>
                  <td><span class="abzeichen {e.aktiv ? 'gut' : 'fehler'}">{e.aktiv ? 'ja' : 'nein'}</span></td>
                  <td>{e.standard_an ? 'ja' : 'nein'}</td>
                </tr>
              {/each}
            </tbody>
          </table>
        {/if}
      </div>
    {/if}
  </div>
</div>

<div class="karte">
  <div class="karte-kopf"><i class="fa-solid fa-sliders"></i> Grenzen</div>
  <div class="karte-inhalt">
    {#if caps}
      <div class="kennzahl-raster">
        <div class="kennzahl"><div class="kz-wert">{caps.grenzen.debounce_ms}</div><div class="kz-name">Entprellung (ms)</div></div>
        <div class="kennzahl"><div class="kz-wert">{caps.grenzen.min_zeichen}</div><div class="kz-name">Min. Zeichen</div></div>
        <div class="kennzahl"><div class="kz-wert">{caps.grenzen.max_vorschlaege}</div><div class="kz-name">Max. Vorschlaege</div></div>
        <div class="kennzahl"><div class="kz-wert">{caps.grenzen.budget_vor}</div><div class="kz-name">Kontext vor (Zeichen)</div></div>
      </div>
    {/if}
  </div>
</div>
