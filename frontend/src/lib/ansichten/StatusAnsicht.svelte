<script lang="ts">
  import { onMount } from 'svelte'

  import { requestJson } from '../api/http'
  import { ladeCapabilities } from '../api/system'
  import type { CapabilitiesAntwort, LernStatus } from '../api/typen'

  let caps = $state<CapabilitiesAntwort | null>(null)
  let lernStatus = $state<LernStatus | null>(null)
  let fehler = $state('')
  let laedt = $state(true)

  async function laden() {
    laedt = true
    fehler = ''
    try {
      caps = await ladeCapabilities()
      lernStatus = await requestJson<LernStatus>('/api/status')
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

<div class="karte">
  <div class="karte-kopf"><i class="fa-solid fa-microchip"></i> Sprachmodell</div>
  <div class="karte-inhalt">
    {#if caps?.llm}
      <p>
        <span class="status-punkt" class:aus={!caps.llm.erreichbar}></span>
        {caps.llm.erreichbar ? 'erreichbar' : 'nicht erreichbar'} unter <code>{caps.llm.url}</code>
      </p>
      {#if caps.llm.modelle.length}
        <p class="hinweis-text">{caps.llm.modelle.length} Modell(e) gemeldet.</p>
      {/if}
    {:else}
      <p class="hinweis-text">Kein Modell-Status verfuegbar.</p>
    {/if}
  </div>
</div>

<div class="karte">
  <div class="karte-kopf"><i class="fa-solid fa-graduation-cap"></i> Lernstand</div>
  <div class="karte-inhalt">
    {#if lernStatus}
      <div class="kennzahl-raster" style="margin-bottom: var(--a3)">
        <div class="kennzahl"><div class="kz-wert">{lernStatus.woerter}</div><div class="kz-name">Gelernte Woerter</div></div>
        <div class="kennzahl"><div class="kz-wert">{lernStatus.ngramme}</div><div class="kz-name">N-Gramme</div></div>
        <div class="kennzahl"><div class="kz-wert">{lernStatus.kontext}</div><div class="kz-name">Kontext-Passagen</div></div>
      </div>
      {#if lernStatus.annahmen.length}
        <table class="tabelle">
          <thead><tr><th>Engine</th><th style="text-align:right">Uebernahmen</th><th style="text-align:right">Ablehnungen</th></tr></thead>
          <tbody>
            {#each lernStatus.annahmen as a (a.engine)}
              <tr><td>{a.engine}</td><td style="text-align:right">{a.uebernahmen}</td><td style="text-align:right">{a.ablehnungen}</td></tr>
            {/each}
          </tbody>
        </table>
      {:else}
        <p class="hinweis-text">Noch keine Uebernahmen erfasst.</p>
      {/if}
    {/if}
  </div>
</div>
