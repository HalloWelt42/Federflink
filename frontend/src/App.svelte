<script lang="ts">
  import { onMount, tick } from 'svelte'

  import { ladeHealth } from './lib/api/system'
  import ErgaenzungAnsicht from './lib/ansichten/ErgaenzungAnsicht.svelte'
  import ProfileAnsicht from './lib/ansichten/ProfileAnsicht.svelte'
  import SpielwieseAnsicht from './lib/ansichten/SpielwieseAnsicht.svelte'
  import StatusAnsicht from './lib/ansichten/StatusAnsicht.svelte'
  import WoerterbuchAnsicht from './lib/ansichten/WoerterbuchAnsicht.svelte'
  import { naechstesTheme, themeZustand } from './lib/theme/theme.svelte'
  import { fassung, fassungVerfolgen, OBERFLAECHE_FASSUNG, vielleichtNeuLaden } from './lib/zustand/fassung.svelte'

  type AnsichtId = 'spielwiese' | 'ergaenzung' | 'woerterbuch' | 'profile' | 'status'
  interface Ansicht {
    id: AnsichtId
    name: string
    icon: string
  }

  const ansichten: Ansicht[] = [
    { id: 'spielwiese', name: 'Rechtschreibung', icon: 'fa-spell-check' },
    { id: 'ergaenzung', name: 'Ergänzung', icon: 'fa-wand-sparkles' },
    { id: 'woerterbuch', name: 'Wörterbuch', icon: 'fa-book' },
    { id: 'profile', name: 'Profile', icon: 'fa-user-pen' },
    { id: 'status', name: 'Status', icon: 'fa-gauge-high' },
  ]

  // Der Reiter steht in der Adresse (#profile): ein Neuladen beim Reiterwechsel landet so auf dem gewählten Reiter.
  function ansichtAusAdresse(): AnsichtId {
    const id = location.hash.slice(1)
    return ansichten.find((a) => a.id === id)?.id ?? 'spielwiese'
  }

  let aktuelleAnsicht = $state<AnsichtId>(ansichtAusAdresse())

  // Erst wechseln, dann nach neuer Fassung schauen: die verlassene Ansicht hat sich dann schon abgemeldet.
  async function adresseGewechselt() {
    aktuelleAnsicht = ansichtAusAdresse()
    await tick()
    vielleichtNeuLaden('ortswechsel')
  }

  let backendOk = $state(false)
  let backendVersion = $state('')

  const themeIcon: Record<string, string> = {
    mittelton: 'fa-circle-half-stroke',
    hell: 'fa-sun',
    dunkel: 'fa-moon',
  }

  async function pruefeBackend() {
    try {
      const h = await ladeHealth()
      backendOk = h.status === 'ok'
      backendVersion = h.version
    } catch {
      backendOk = false
    }
  }

  onMount(() => {
    void pruefeBackend()
    const timer = setInterval(pruefeBackend, 5000)
    const fassungStoppen = fassungVerfolgen()
    addEventListener('hashchange', adresseGewechselt)
    return () => {
      clearInterval(timer)
      fassungStoppen()
      removeEventListener('hashchange', adresseGewechselt)
    }
  })
</script>

<div class="app">
  <header class="kopf">
    <span class="marke">
      <i class="fa-solid fa-feather-pointed"></i>
      Federflink
      <span class="version">v{OBERFLAECHE_FASSUNG}</span>
    </span>

    <nav class="kopf-nav">
      {#each ansichten as ansicht (ansicht.id)}
        <button
          class="reiter"
          class:aktiv={aktuelleAnsicht === ansicht.id}
          onclick={() => (location.hash = ansicht.id)}
        >
          <i class="fa-solid {ansicht.icon}"></i>
          {ansicht.name}
        </button>
      {/each}
    </nav>

    <div class="kopf-rechts">
      <button
        class="icon-knopf"
        title="Erscheinungsbild wechseln"
        aria-label="Erscheinungsbild wechseln"
        onclick={naechstesTheme}
      >
        <i class="fa-solid {themeIcon[themeZustand.aktuell]}"></i>
      </button>
    </div>
  </header>

  <main class="haupt">
    <div class="inhalt">
      {#if fassung.neu}
        <div class="band" role="status">
          <i class="fa-solid fa-rotate"></i>
          <span>
            <strong>Neue Fassung {fassung.neu} ist da.</strong>
            Beim nächsten Reiterwechsel lädt Federflink sie von selbst.
          </span>
          <button class="knopf primaer klein" onclick={() => location.reload()}>
            <i class="fa-solid fa-rotate"></i> Jetzt neu laden
          </button>
        </div>
      {/if}
      {#if aktuelleAnsicht === 'spielwiese'}
        <SpielwieseAnsicht />
      {:else if aktuelleAnsicht === 'ergaenzung'}
        <ErgaenzungAnsicht />
      {:else if aktuelleAnsicht === 'woerterbuch'}
        <WoerterbuchAnsicht />
      {:else if aktuelleAnsicht === 'profile'}
        <ProfileAnsicht />
      {:else if aktuelleAnsicht === 'status'}
        <StatusAnsicht />
      {/if}
    </div>
  </main>

  <footer class="status">
    <span class="status-punkt" class:aus={!backendOk}></span>
    <span>{backendOk ? `Backend verbunden (v${backendVersion})` : 'Backend nicht erreichbar'}</span>
    <div class="status-rechts">
      <span>Federflink - Rechtschreibung und Textergänzung</span>
    </div>
  </footer>
</div>
