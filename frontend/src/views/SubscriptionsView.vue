<script setup lang="ts">
/**
 * SubscriptionsView - Displays detected recurring subscriptions with analytics.
 *
 * Features:
 * - Summary statistics: active/inactive counts, monthly total, yearly projection
 * - Detailed list of subscriptions with merchant, category, amount, cadence, next charge, status
 * - Loading and empty states
 * - Utilizes existing API endpoint and types
 */
import { ref, onMounted, watch } from 'vue'
import { statsApi } from '@/api'
import type { Subscription, SubscriptionsResponse } from '@/types'
import { formatCurrency, formatDate, categoryBadgeStyle } from '@/utils/formatters'
import { Card, CardContent } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'
import { Table, TableHeader, TableBody, TableHead, TableRow, TableCell } from '@/components/ui/table'
import { Badge } from '@/components/ui/badge'
import { Repeat } from 'lucide-vue-next'

/** Subscription data */
const subscriptions = ref<Subscription[]>([])
/** Summary statistics */
const summary = ref<SubscriptionsResponse['summary'] | null>(null)
/** Loading state */
const loading = ref(true)

/**
 * Fetch subscription data from the API
 */
async function loadData() {
  loading.value = true
  try {
    const response = await statsApi.subscriptions()
    summary.value = response.data.summary
    subscriptions.value = response.data.items
  } catch (error) {
  } finally {
    loading.value = false
  }
}

/** Translate cadence to Italian */
function getCadenceLabel(cadence: Subscription['cadence']): string {
  const labels: Record<Subscription['cadence'], string> = {
    weekly: 'Settimanale',
    monthly: 'Mensile',
    quarterly: 'Trimestrale',
    yearly: 'Annuale',
    irregular: 'Irregolare',
  }
  return labels[cadence]
}

/** Get status badge variant based on active state */
function getStatusVariant(isActive: boolean): Badge['variant'] {
  return isActive ? 'default' : 'secondary'
}

// Fetch data on initial mount
onMounted(loadData)
</script>

<template>
  <div>
    <div class="mb-6 flex flex-wrap items-center justify-between gap-4">
      <h1 class="text-2xl font-bold tracking-tight">Abbonamenti</h1>
      <span class="text-sm text-muted-foreground">
        {{ summary?.active_count }} attivi, {{ summary?.inactive_count }} inattivi
      </span>
    </div>

    <!-- Summary Cards -->
    <template v-if="summary">
      <Card class="mb-6">
        <CardContent class="pt-6">
          <div class="grid grid-cols-1 gap-4 sm:grid-cols-4">
            <!-- Active Count -->
            <div class="text-center">
              <p class="text-xs font-medium text-muted-foreground">Attivi</p>
              <p class="text-2xl font-semibold">{{ summary.active_count }}</p>
            </div>
            <!-- Inactive Count -->
            <div class="text-center">
              <p class="text-xs font-medium text-muted-foreground">Inattivi</p>
              <p class="text-2xl font-semibold">{{ summary.inactive_count }}</p>
            </div>
            <!-- Monthly Total -->
            <div class="text-center">
              <p class="text-xs font-medium text-muted-foreground">Spesa Mensile</p>
              <p class="text-2xl font-semibold">{{ formatCurrency(summary.monthly_total) }}</p>
            </div>
            <!-- Yearly Projection -->
            <div class="text-center">
              <p class="text-xs font-medium text-muted-foreground">Proiezione Annuale</p>
              <p class="text-2xl font-semibold">{{ formatCurrency(summary.yearly_projection) }}</p>
            </div>
          </div>
        </CardContent>
      </Card>
    </template>

    <template v-if="loading">
      <div class="space-y-3">
        <Skeleton v-for="i in 4" :key="i" class="h-12" />
      </div>
    </template>
    <template v-else-if="!subscriptions.length">
      <Card>
        <CardContent class="py-12 text-center">
          <p class="text-muted-foreground">Nessun abbonamento ricorrente rilevato</p>
        </CardContent>
      </Card>
    </template>
    <template v-else>
      <Card>
        <CardContent class="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead class="w-32">Commerciante</TableHead>
                <TableHead class="w-24">Categoria</TableHead>
                <TableHead class="w-20 text-right">Importo</TableHead>
                <TableHead>Cadenza</TableHead>
                <TableHead class="w-24">Prossimo Addebito</TableHead>
                <TableHead class="w-16">Stato</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              <template v-for="sub in subscriptions" :key="sub.merchant">
                <TableRow>
                  <TableCell class="whitespace-nowrap font-medium">
                    {{ sub.merchant }}
                  </TableCell>
                  <TableCell>
                    <template v-if="sub.category">
                      <Badge
                        :style="categoryBadgeStyle(sub.color)"
                        variant="secondary"
                      >
                        {{ sub.category }}
                      </Badge>
                    </template>
                    <template v-else>
                      <span class="text-muted-foreground">—</span>
                    </template>
                  </TableCell>
                  <TableCell class="whitespace-nowrap text-right font-mono tabular-nums font-medium">
                    {{ formatCurrency(sub.avg_amount) }}
                  </TableCell>
                  <TableCell>
                    {{ getCadenceLabel(sub.cadence) }}
                  </TableCell>
                  <TableCell class="whitespace-nowrap">
                    {{ formatDate(sub.next_expected) }}
                  </TableCell>
                  <TableCell>
                    <Badge :variant="getStatusVariant(sub.is_active)">
                      {{ sub.is_active ? 'Attivo' : 'Inattivo' }}
                    </Badge>
                  </TableCell>
                </TableRow>
              </template>
            </TableBody>
          </Table>
        </CardContent>
      </Card>
    </template>
  </div>
</template>