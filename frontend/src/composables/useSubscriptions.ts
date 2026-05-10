import { onMounted, ref } from 'vue'
import { statsApi } from '@/api'
import type { Subscription, SubscriptionsResponse } from '@/types'
import type { BadgeVariants } from '@/components/ui/badge'

export function useSubscriptions() {
  const subscriptions = ref<Subscription[]>([])
  const summary = ref<SubscriptionsResponse['summary'] | null>(null)
  const loading = ref(true)
  const savingKey = ref<string | null>(null)

  async function loadData() {
    loading.value = true
    try {
      const response = await statsApi.subscriptions()
      subscriptions.value = response.data.items.filter((s) => s.is_active)
      summary.value = response.data.summary
      recomputeSummary()
    } catch (error) {
      console.error('Caricamento abbonamenti fallito:', error)
    } finally {
      loading.value = false
    }
  }

  function recomputeSummary() {
    const active = subscriptions.value.filter((s) => s.is_active).length
    const monthlyTotal = subscriptions.value
      .filter((s) => s.is_active)
      .reduce((acc, s) => acc + (s.monthly_equivalent || 0), 0)

    summary.value = {
      active_count: active,
      inactive_count: 0,
      monthly_total: Number(monthlyTotal.toFixed(2)),
      yearly_projection: Number((monthlyTotal * 12).toFixed(2)),
      total_paid_12m: summary.value?.total_paid_12m ?? 0,
    }
  }

  async function sendFeedback(sub: Subscription, decision: 'CONFIRMED' | 'REJECTED') {
    savingKey.value = sub.cluster_key
    try {
      await statsApi.subscriptionsFeedback({
        cluster_key: sub.cluster_key,
        decision,
        canonical_merchant_override: null,
      })
      if (decision === 'CONFIRMED') {
        const idx = subscriptions.value.findIndex((s) => s.cluster_key === sub.cluster_key)
        if (idx >= 0) {
          const current = subscriptions.value[idx]
          if (current) {
            subscriptions.value[idx] = { ...current, review_status: 'confirmed' }
          }
        }
      } else {
        subscriptions.value = subscriptions.value.filter((s) => s.cluster_key !== sub.cluster_key)
      }
      recomputeSummary()
    } finally {
      savingKey.value = null
    }
  }

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

  function getStatusVariant(isActive: boolean): BadgeVariants['variant'] {
    return isActive ? 'default' : 'secondary'
  }

  function getReviewBadge(
    status: Subscription['review_status'],
  ): { label: string; variant: BadgeVariants['variant'] } {
    if (status === 'confirmed') return { label: 'Confermato', variant: 'default' }
    if (status === 'needs_review') return { label: 'Da revisionare', variant: 'secondary' }
    return { label: 'Proposto', variant: 'secondary' }
  }

  function formatConfidence(confidence: number | null): string {
    if (confidence === null || Number.isNaN(confidence)) return '—'
    return `${Math.round(confidence * 100)}%`
  }

  onMounted(loadData)

  return {
    subscriptions,
    summary,
    loading,
    savingKey,
    sendFeedback,
    getCadenceLabel,
    getStatusVariant,
    getReviewBadge,
    formatConfidence,
  }
}
