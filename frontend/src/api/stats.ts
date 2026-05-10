import { api } from './client'
import type {
  BalancePoint,
  CategoryComparison,
  CategoryStats,
  MonthlyTrend,
  StatsSummary,
  SubscriptionsResponse,
  TopMerchant,
} from '@/types'

export const statsApi = {
  summary: (params?: Record<string, string>) => api.get<StatsSummary>('/stats/summary/', { params }),
  byCategory: (params?: Record<string, string>) => api.get<CategoryStats[]>('/stats/by-category/', { params }),
  monthly: (params?: Record<string, string>) => api.get<MonthlyTrend[]>('/stats/monthly/', { params }),
  topMerchants: (params?: Record<string, string>) => api.get<TopMerchant[]>('/stats/top-merchants/', { params }),
  balance: () => api.get<BalancePoint[]>('/stats/balance/'),
  comparison: (params?: Record<string, string>) => api.get<CategoryComparison[]>('/stats/comparison/', { params }),
  subscriptions: () => api.get<SubscriptionsResponse>('/stats/subscriptions/'),
  subscriptionsFeedback: (data: {
    cluster_key: string
    decision: 'CONFIRMED' | 'REJECTED'
    canonical_merchant_override?: string | null
  }) => api.post('/stats/subscriptions/feedback/', data),
}
