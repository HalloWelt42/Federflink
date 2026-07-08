<script lang="ts">
  import { onMount } from 'svelte'

  import { ladeHealth } from './lib/api/system'
  import ErgaenzungAnsicht from './lib/ansichten/ErgaenzungAnsicht.svelte'
  import ProfileAnsicht from './lib/ansichten/ProfileAnsicht.svelte'
  import SpielwieseAnsicht from './lib/ansichten/SpielwieseAnsicht.svelte'
  import StatusAnsicht from './lib/ansichten/StatusAnsicht.svelte'
  import WoerterbuchAnsicht from './lib/ansichten/WoerterbuchAnsicht.svelte'
  import { naechstesTheme, themeZustand } from './lib/theme/theme.svelte'

  const version = __APP_VERSION__

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

  let aktuelleAnsicht = $state<AnsichtId>('spielwiese')

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
    return () => clearInterval(timer)
  })
</script>

<div class="app">
  <header class="kopf">
    <span class="marke">
      <i class="fa-solid fa-feather-pointed"></i>
      Federflink
      <span class="version">v{version}</span>
    </span>

    <nav class="kopf-nav">
      {#each ansichten as ansicht (ansicht.id)}
        <button
          class="reiter"
          class:aktiv={aktuelleAnsicht === ansicht.id}
          onclick={() => (aktuelleAnsicht = ansicht.id)}
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
