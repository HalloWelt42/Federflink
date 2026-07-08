import '@fontsource/barlow/400.css'
import '@fontsource/barlow/500.css'
import '@fontsource/barlow/600.css'
import '@fontsource/jetbrains-mono/400.css'
import '@fortawesome/fontawesome-free/css/all.min.css'

import './lib/theme/tokens.css'
import './app.css'

import { mount } from 'svelte'

import App from './App.svelte'
import { initTheme } from './lib/theme/theme.svelte'

initTheme()

const ziel = document.getElementById('app')
if (!ziel) {
  throw new Error('Wurzelelement #app fehlt in index.html')
}

const app = mount(App, { target: ziel })

export default app
