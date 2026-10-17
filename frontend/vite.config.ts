import { svelte } from '@sveltejs/vite-plugin-svelte'
import { defineConfig } from 'vite'

import fassungDatei from '../version.json'

// Backend-Port: start.sh setzt FEDERFLINK_API_PORT, falls 8500 belegt ist und das
// Backend auf einen freien Port ausweicht. Default bleibt 8500.
const apiPort = process.env.FEDERFLINK_API_PORT ?? '8500'
const apiZiel = `http://localhost:${apiPort}`

// Fassung der Oberfläche aus der einzigen Quelle (version.json); weicht die des Servers ab, lädt die Oberfläche neu
// (src/lib/zustand/fassung.svelte.ts). Als Import zählt version.json zu den Abhängigkeiten der Konfiguration: ändert
// sie sich, startet der Entwicklungsserver von selbst neu, und eingebaute und Server-Fassung bleiben gleich.
export default defineConfig({
  define: {
    __FASSUNG__: JSON.stringify(fassungDatei.version),
  },
  plugins: [svelte()],
  server: {
    port: 5195,
    strictPort: true,
    proxy: {
      '/api': { target: apiZiel, changeOrigin: true },
      '/docs': { target: apiZiel, changeOrigin: true },
      '/openapi.json': { target: apiZiel, changeOrigin: true },
    },
  },
})
