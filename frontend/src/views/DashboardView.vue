<script setup lang="ts">
/**
 * DashboardView - Main dashboard displaying financial overview with charts and summaries.
 *
 * Fetches and displays:
 * - Summary cards (total expenses, total income, net balance)
 * - Donut chart of expenses by category
 * - Top 5 merchants by spending
 * - 12-month trend bar chart
 * - Category comparison with previous period
 *
 * The time period (month/quarter/year) is selectable via a toggle group.
 * Data is fetched in parallel on mount and whenever the period changes.
 */
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
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { ToggleGroup, ToggleGroupItem } from '@/components/ui/toggle-group'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import { TrendingUp, TrendingDown, ArrowLeftRight, Wallet } from 'lucide-vue-next'

/** Selected time period for stats filtering: 'month' | 'quarter' | 'year' */
const period = ref('month')
/** Overall summary: total expenses, income, net balance, transaction count */
const summary = ref<StatsSummary | null>(null)
/** Expense breakdown by category for the donut chart */
const byCategory = ref<CategoryStats[]>([])
/** 12-month spending trend data for the bar chart */
const monthly = ref<MonthlyTrend[]>([])
/** Top 5 merchants by total spending */
const topMerchants = ref<TopMerchant[]>([])
/** Category spending comparison with the previous period (includes change percentage) */
const comparison = ref<CategoryComparison[]>([])
/** Loading state for the initial fetch and period changes */
const loading = ref(true)

/**
 * Fetches all dashboard data in parallel from the stats API.
 * Uses the currently selected `period` for period-scoped endpoints.
 * The monthly trend always returns 12 months regardless of period.
 */
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

// Fetch data on initial mount
onMounted(loadData)
// Re-fetch whenever the selected period changes
watch(period, loadData)

/** Options for the period toggle group UI */
const periodOptions = [
  { value: 'month', label: 'Mese' },
  { value: 'quarter', label: 'Trimestre' },
  { value: 'year', label: 'Anno' },
]
</script>

<template>
  <div>
    <div class="mb-6 flex flex-wrap items-center justify-between gap-4">
      <h1 class="text-2xl font-bold tracking-tight">Dashboard</h1>
      <ToggleGroup
        type="single"
        :model-value="period"
        variant="outline"
        @update:model-value="period = ($event as string)"
      >
        <ToggleGroupItem
          v-for="opt in periodOptions"
          :key="opt.value"
          :value="opt.value"
        >
          {{ opt.label }}
        </ToggleGroupItem>
      </ToggleGroup>
    </div>

    <template v-if="loading">
      <div class="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Skeleton v-for="i in 3" :key="i" class="h-32" />
      </div>
    </template>
    <template v-else>
      <div v-if="summary" class="mb-6 grid grid-cols-1 gap-4 sm:grid-cols-3">
        <Card class="border-l-4 border-l-expense">
          <CardHeader class="pb-2">
            <CardDescription class="flex items-center gap-1.5">
              <TrendingDown class="size-4" />
              Spese totali
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div class="text-2xl font-bold font-mono tabular-nums text-expense">
              {{ formatCurrency(summary.total_expenses) }}
            </div>
            <p class="text-xs text-muted-foreground">{{ summary.transaction_count }} transazioni</p>
          </CardContent>
        </Card>

        <Card class="border-l-4 border-l-income">
          <CardHeader class="pb-2">
            <CardDescription class="flex items-center gap-1.5">
              <TrendingUp class="size-4" />
              Entrate totali
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div class="text-2xl font-bold font-mono tabular-nums text-income">
              {{ formatCurrency(summary.total_income) }}
            </div>
          </CardContent>
        </Card>

        <Card class="border-l-4 border-l-primary">
          <CardHeader class="pb-2">
            <CardDescription class="flex items-center gap-1.5">
              <Wallet class="size-4" />
              Saldo netto
            </CardDescription>
          </CardHeader>
          <CardContent>
            <div
              class="text-2xl font-bold font-mono tabular-nums"
              :class="summary.net >= 0 ? 'text-income' : 'text-expense'"
            >
              {{ formatCurrency(summary.net) }}
            </div>
          </CardContent>
        </Card>
      </div>

      <div class="mb-6 grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle class="text-base">Spese per categoria</CardTitle>
          </CardHeader>
          <CardContent>
            <DonutChart v-if="byCategory.length" :data="byCategory" />
            <p v-else class="py-8 text-center text-sm text-muted-foreground">Nessun dato nel periodo</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle class="text-base">Top 5 merchant</CardTitle>
          </CardHeader>
          <CardContent>
            <div v-if="topMerchants.length">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead class="w-10">#</TableHead>
                    <TableHead>Merchant</TableHead>
                    <TableHead class="text-right">Totale</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  <TableRow v-for="(m, i) in topMerchants" :key="i">
                    <TableCell class="font-mono tabular-nums text-muted-foreground">
                      {{ i + 1 }}
                    </TableCell>
                    <TableCell class="font-medium">{{ m.merchant }}</TableCell>
                    <TableCell class="text-right font-mono tabular-nums text-expense">
                      {{ formatCurrency(m.total) }}
                    </TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </div>
            <p v-else class="py-8 text-center text-sm text-muted-foreground">Nessun dato nel periodo</p>
          </CardContent>
        </Card>
      </div>

      <div class="mb-6 grid grid-cols-1 gap-6 lg:grid-cols-2">
        <Card>
          <CardHeader>
            <CardTitle class="text-base">Andamento mensile (12 mesi)</CardTitle>
          </CardHeader>
          <CardContent>
            <BarChart v-if="monthly.length" :data="monthly" />
            <p v-else class="py-8 text-center text-sm text-muted-foreground">Nessun dato disponibile</p>
          </CardContent>
        </Card>

        <Card>
          <CardHeader>
            <CardTitle class="text-base">Confronto con periodo precedente</CardTitle>
          </CardHeader>
          <CardContent>
            <div v-if="comparison.length">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Categoria</TableHead>
                    <TableHead class="text-right">Variazione</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  <TableRow
                    v-for="c in comparison.filter((x) => x.change_pct !== null).slice(0, 8)"
                    :key="c.category"
                  >
                    <TableCell>
                      <div class="flex items-center gap-2">
                        <span class="size-3 rounded-full" :style="{ backgroundColor: c.color }" />
                        <span>{{ c.category }}</span>
                      </div>
                    </TableCell>
                    <TableCell class="text-right">
                      <Badge
                        :variant="c.change_pct && c.change_pct > 0 ? 'destructive' : 'secondary'"
                      >
                        {{ c.change_pct && c.change_pct > 0 ? '+' : '' }}{{ c.change_pct }}%
                      </Badge>
                    </TableCell>
                  </TableRow>
                </TableBody>
              </Table>
            </div>
            <p v-else class="py-8 text-center text-sm text-muted-foreground">Nessun dato disponibile</p>
          </CardContent>
        </Card>
      </div>
    </template>
  </div>
</template>