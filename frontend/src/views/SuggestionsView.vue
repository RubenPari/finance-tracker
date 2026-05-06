<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { suggestionsApi } from '@/api'
import type { Suggestion } from '@/types'
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'

const suggestions = ref<Suggestion[]>([])
const loading = ref(true)

async function loadSuggestions() {
  loading.value = true
  try {
    const { data } = await suggestionsApi.list()
    suggestions.value = data
  } finally {
    loading.value = false
  }
}

function typeIcon(type: string) {
  const icons: Record<string, string> = {
    biggest_increase: '📈',
    subscription: '🔄',
    spending_peaks: '⚡',
    outlier: '⚠️',
  }
  return icons[type] || '💡'
}

function typeColor(type: string) {
  const colors: Record<string, string> = {
    biggest_increase: 'border-l-orange-500',
    subscription: 'border-l-purple-500',
    spending_peaks: 'border-l-yellow-500',
    outlier: 'border-l-red-500',
  }
  return colors[type] || 'border-l-blue-500'
}

onMounted(loadSuggestions)
</script>

<template>
  <div>
    <div class="mb-6 flex flex-wrap items-center justify-between gap-4">
      <h1 class="text-2xl font-bold text-gray-900">Suggerimenti</h1>
      <button class="btn-secondary text-sm" @click="loadSuggestions">Aggiorna</button>
    </div>

    <LoadingSpinner v-if="loading" />
    <div v-else-if="!suggestions.length" class="card py-16 text-center">
      <span class="text-4xl">🎉</span>
      <h2 class="mt-3 text-lg font-semibold text-gray-900">Tutto sotto controllo!</h2>
      <p class="mt-1 text-sm text-gray-400">
        Non ci sono suggerimenti al momento. Importa più transazioni per ricevere consigli.
      </p>
    </div>

    <div v-else class="grid grid-cols-1 gap-4 lg:grid-cols-2">
      <div
        v-for="(s, i) in suggestions"
        :key="i"
        class="card border-l-4"
        :class="typeColor(s.type)"
      >
        <div class="flex items-start gap-3">
          <span class="text-2xl">{{ typeIcon(s.type) }}</span>
          <div>
            <h3 class="font-semibold text-gray-900">{{ s.title }}</h3>
            <p class="mt-1 text-sm text-gray-600">{{ s.message }}</p>
          </div>
        </div>

        <div v-if="s.type === 'biggest_increase' && typeof s.change_pct === 'number'" class="mt-3">
          <span
            class="inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium"
            :style="{
              backgroundColor: `${s.color}20` as string,
              color: s.color as string,
            }"
          >
            +{{ s.change_pct }}%
          </span>
        </div>
      </div>
    </div>
  </div>
</template>
