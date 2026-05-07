<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { suggestionsApi } from '@/api'
import type { Suggestion } from '@/types'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { TrendingUp, RotateCw, Zap, AlertTriangle, Lightbulb, RefreshCw } from 'lucide-vue-next'

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
  const icons: Record<string, typeof TrendingUp> = {
    biggest_increase: TrendingUp,
    subscription: RotateCw,
    spending_peaks: Zap,
    outlier: AlertTriangle,
  }
  return icons[type] || Lightbulb
}

function typeBorderClass(type: string): string {
  const map: Record<string, string> = {
    biggest_increase: 'border-l-income',
    subscription: 'border-l-purple-500',
    spending_peaks: 'border-l-warning',
    outlier: 'border-l-destructive',
  }
  return map[type] || 'border-l-primary'
}

onMounted(loadSuggestions)
</script>

<template>
  <div>
    <div class="mb-6 flex flex-wrap items-center justify-between gap-4">
      <h1 class="text-2xl font-bold tracking-tight">Suggerimenti</h1>
      <Button variant="outline" size="sm" @click="loadSuggestions">
        <RefreshCw class="mr-2 size-4" />
        Aggiorna
      </Button>
    </div>

    <template v-if="loading">
      <div class="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Skeleton v-for="i in 4" :key="i" class="h-32" />
      </div>
    </template>
    <template v-else-if="!suggestions.length">
      <Card class="py-16 text-center">
        <CardContent>
          <Lightbulb class="mx-auto size-10 text-muted-foreground" />
          <h2 class="mt-3 text-lg font-semibold">Tutto sotto controllo!</h2>
          <p class="mt-1 text-sm text-muted-foreground">
            Non ci sono suggerimenti al momento. Importa più transazioni per ricevere consigli.
          </p>
        </CardContent>
      </Card>
    </template>
    <template v-else>
      <div class="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card
          v-for="(s, i) in suggestions"
          :key="i"
          class="border-l-4"
          :class="typeBorderClass(s.type)"
        >
          <CardContent class="pt-6">
            <div class="flex items-start gap-3">
              <component :is="typeIcon(s.type)" class="mt-0.5 size-5 shrink-0 text-muted-foreground" />
              <div>
                <h3 class="font-semibold">{{ s.title }}</h3>
                <p class="mt-1 text-sm text-muted-foreground">{{ s.message }}</p>
              </div>
            </div>

            <div v-if="s.type === 'biggest_increase' && typeof s.change_pct === 'number'" class="mt-3">
              <Badge variant="destructive">
                +{{ s.change_pct }}%
              </Badge>
            </div>
          </CardContent>
        </Card>
      </div>
    </template>
  </div>
</template>