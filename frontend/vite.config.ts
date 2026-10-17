import { readFileSync } from 'node:fs'
import { fileURLToPath } from 'node:url'

import { svelte } from '@sveltejs/vite-plugin-svelte'
import { defineConfig, type Plugin } from 'vite'

// Backend-Port: start.sh setzt FEDERFLINK_API_PORT, falls 8500 belegt ist und das
// Backend auf einen freien Port ausweicht. Default bleibt 8500.
const apiPort = process.env.FEDERFLINK_API_PORT ?? '8500'
const apiZiel = `http://localhost:${apiPort}`

// Fassung der Oberfläche aus der einzigen Quelle (version.json); weicht die des Servers ab, lädt die Oberfläche neu.
const VERSIONSDATEI = fileURLToPath(new URL('../version.json', import.meta.url))
const FASSUNG = (JSON.parse(readFileSync(VERSIONSDATEI, 'utf-8')) as { version: string }).version

// Die Oberfläche läuft im Betrieb über den Entwicklungsserver; die eingebaute Fassung steht nur beim Start fest.
// Ändert sich version.json, startet der Server neu, damit eingebaute und Server-Fassung nicht auseinanderlaufen.
function fassungBeobachten(): Plugin {
  return {
    name: 'federflink-fassung',
    configureServer(server) {
      server.watcher.add(VERSIONSDATEI)
      server.watcher.on('change', (pfad) => {
        if (pfad === VERSIONSDATEI) void server.restart()
      })
    },
  }
}

export default defineConfig({
  define: {
    __FASSUNG__: JSON.stringify(FASSUNG),
  },
  plugins: [svelte(), fassungBeobachten()],
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
