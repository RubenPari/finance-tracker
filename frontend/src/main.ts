/**
 * Application entry point.
 *
 * Initialises the Vue 3 application with Pinia for state management,
 * Vue Router for client-side routing, and mounts to the `#app` element.
 * Global styles are imported from `assets/main.css`.
 */
import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import router from './router'
import './assets/main.css'

const app = createApp(App)

// Register Pinia (state management) and Vue Router (navigation)
app.use(createPinia())
app.use(router)

// Mount the Vue application to the DOM element with id="app"
app.mount('#app')
