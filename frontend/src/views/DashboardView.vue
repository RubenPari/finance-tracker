<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { statsApi } from '@/api'
import type {
  StatsSummary,
  CategoryStats,
  MonthlyTrend,
  TopMerchant,
  CategoryComparison,
} from '@/types'
import { DonutChart, BarChart } from '@/components/dashboard'
import { formatCurrency } from '@/utils/formatters'
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'

const period = ref('month')
const summary = ref<StatsSummary | null>(null)
const byCategory = ref<CategoryStats[]>([])
const monthly = ref<MonthlyTrend[]>([])
const topMerchants = ref<TopMerchant[]>([])
const comparison = ref<CategoryComparison[]>([])
const loading = ref(true)

async function loadData() {
  loading.value = true
  try {
    const params = { period: period.value }
    const [s, cat, mon, top, comp] = await Promise.all([
      statsApi.summary(params),
      statsApi.byCategory(params),
      statsApi.monthly({ months: '12' }),
      statsApi.topMerchants(params),
      statsApi.comparison(params),
    ])
    summary.value = s.data
    byCategory.value = cat.data
    monthly.value = mon.data
    topMerchants.value = top.data
    comparison.value = comp.data
  } finally {
    loading.value = false
  }
}

onMounted(loadData)
watch(period, loadData)

const periodOptions = [
  { value: 'month', label: 'Mese corrente' },
  { value: 'quarter', label: 'Trimestre' },
  { value: 'year', label: 'Anno' },
]
</script>

<template>
  <div>
    <div class="mb-6 flex flex-wrap items-center justify-between gap-4">
      <h1 class="text-2xl font-bold text-gray-900">Dashboard</h1>
      <div class="flex gap-2">
        <button
          v-for="opt in periodOptions"
          :key="opt.value"
          :class="period === opt.value ? 'btn-primary' : 'btn-secondary'"
          @click="period = opt.value"
        >
          {{ opt.label }}
        </button>
      </div>
    </div>

    <LoadingSpinner v-if="loading" />
    <template v-else>
      <div v-if="summary" class="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-3">
        <div class="card">
          <p class="text-sm text-gray-500">Spese totali</p>
          <p class="mt-1 text-2xl font-bold text-red-600">
            {{ formatCurrency(summary.total_expenses) }}
          </p>
          <p class="text-xs text-gray-400">{{ summary.transaction_count }} transazioni</p>
        </div>
        <div class="card">
          <p class="text-sm text-gray-500">Entrate totali</p>
          <p class="mt-1 text-2xl font-bold text-green-600">
            {{ formatCurrency(summary.total_income) }}
          </p>
        </div>
        <div class="card">
          <p class="text-sm text-gray-500">Saldo netto</p>
          <p
            class="mt-1 text-2xl font-bold"
            :class="summary.net >= 0 ? 'text-blue-600' : 'text-red-600'"
          >
            {{ formatCurrency(summary.net) }}
          </p>
        </div>
      </div>

      <div class="mb-6 grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div class="card">
          <h2 class="mb-4 text-lg font-semibold text-gray-900">Spese per categoria</h2>
          <DonutChart v-if="byCategory.length" :data="byCategory" />
          <p v-else class="py-8 text-center text-sm text-gray-400">Nessun dato nel periodo</p>
        </div>

        <div class="card">
          <h2 class="mb-4 text-lg font-semibold text-gray-900">Top 5 merchant</h2>
          <div v-if="topMerchants.length" class="space-y-3">
            <div
              v-for="(m, i) in topMerchants"
              :key="i"
              class="flex items-center justify-between rounded-lg bg-gray-50 px-4 py-3"
            >
              <div>
                <span class="mr-2 text-sm font-medium text-gray-500">#{{ i + 1 }}</span>
                <span class="text-sm font-medium text-gray-900">{{ m.merchant }}</span>
              </div>
              <span class="text-sm font-semibold text-red-600">{{ formatCurrency(m.total) }}</span>
            </div>
          </div>
          <p v-else class="py-8 text-center text-sm text-gray-400">Nessun dato nel periodo</p>
        </div>
      </div>

      <div class="mb-6 grid grid-cols-1 gap-6 lg:grid-cols-2">
        <div class="card">
          <h2 class="mb-4 text-lg font-semibold text-gray-900">Andamento mensile (12 mesi)</h2>
          <BarChart v-if="monthly.length" :data="monthly" />
          <p v-else class="py-8 text-center text-sm text-gray-400">Nessun dato disponibile</p>
        </div>

        <div class="card">
          <h2 class="mb-4 text-lg font-semibold text-gray-900">Confronto con periodo precedente</h2>
          <div v-if="comparison.length" class="space-y-2">
            <div
              v-for="c in comparison.filter((x) => x.change_pct !== null).slice(0, 8)"
              :key="c.category"
              class="flex items-center justify-between rounded-lg bg-gray-50 px-4 py-2"
            >
              <div class="flex items-center gap-2">
                <span class="h-3 w-3 rounded-full" :style="{ backgroundColor: c.color }" />
                <span class="text-sm text-gray-900">{{ c.category }}</span>
              </div>
              <span
                class="text-sm font-medium"
                :class="c.change_pct && c.change_pct > 0 ? 'text-red-600' : 'text-green-600'"
              >
                {{ c.change_pct && c.change_pct > 0 ? '+' : '' }}{{ c.change_pct }}%
              </span>
            </div>
          </div>
          <p v-else class="py-8 text-center text-sm text-gray-400">Nessun dato disponibile</p>
        </div>
      </div>
    </template>
  </div>
</template>
