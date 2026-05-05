<script setup lang="ts">
import { useRoute } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const route = useRoute()
const auth = useAuthStore()

const navItems = [
  { path: '/dashboard', label: 'Dashboard', icon: '📊' },
  { path: '/transactions', label: 'Transazioni', icon: '💳' },
  { path: '/import', label: 'Importa CSV', icon: '📥' },
  { path: '/categories', label: 'Categorie', icon: '🏷️' },
  { path: '/budgets', label: 'Budget', icon: '💰' },
  { path: '/suggestions', label: 'Suggerimenti', icon: '💡' },
]
</script>

<template>
  <div class="flex h-screen overflow-hidden bg-gray-50">
    <aside class="hidden w-64 flex-shrink-0 border-r border-gray-200 bg-white md:flex md:flex-col">
      <div class="flex h-16 items-center gap-2 border-b border-gray-200 px-4">
        <span class="text-xl">📊</span>
        <span class="text-lg font-semibold text-gray-900">Finance Tracker</span>
      </div>

      <nav class="flex-1 space-y-1 overflow-y-auto p-3">
        <RouterLink
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          :class="route.path.startsWith(item.path) ? 'sidebar-link-active' : 'sidebar-link'"
        >
          <span>{{ item.icon }}</span>
          {{ item.label }}
        </RouterLink>
      </nav>

      <div class="border-t border-gray-200 p-3">
        <div class="sidebar-link mb-2 text-xs">
          {{ auth.user?.email }}
        </div>
        <button class="btn-secondary w-full" @click="auth.logout()">
          Esci
        </button>
      </div>
    </aside>

    <div class="flex flex-1 flex-col overflow-hidden">
      <header
        class="flex h-16 items-center justify-between border-b border-gray-200 bg-white px-6 md:hidden"
      >
        <span class="text-lg font-semibold">📊 Finance Tracker</span>
        <button class="btn-secondary text-sm" @click="auth.logout()">Esci</button>
      </header>

      <main class="flex-1 overflow-y-auto p-6">
        <RouterView />
      </main>
    </div>
  </div>
</template>
