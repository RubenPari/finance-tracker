import axios from 'axios'
import { useAuthStore } from '@/stores/auth'
import type {
  AuthResponse,
  Transaction,
  TransactionFilters,
  Category,
  CategoryRule,
  Budget,
  ImportBatch,
  StatsSummary,
  CategoryStats,
  MonthlyTrend,
  TopMerchant,
  BalancePoint,
  CategoryComparison,
  Suggestion,
  PaginatedResponse,
} from '@/types'

const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
})

const refreshClient = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use((config) => {
  const store = useAuthStore()
  if (store.accessToken) {
    config.headers.Authorization = `Bearer ${store.accessToken}`
  }
  return config
})

api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const store = useAuthStore()
    const original = error.config

    if (error.response?.status === 401 && !original._retry && store.refreshToken) {
      original._retry = true
      try {
        const { data } = await refreshClient.post('/auth/refresh/', {
          refresh: store.refreshToken,
        })
        store.setTokens(data.access, data.refresh)
        original.headers.Authorization = `Bearer ${data.access}`
        return api(original)
      } catch {
        store.logout()
        window.location.href = '/login'
      }
    }
    return Promise.reject(error)
  },
)

export const authApi = {
  login: (email: string, password: string) =>
    api.post<AuthResponse>('/auth/login/', { email, password }),
  register: (data: Record<string, string>) => api.post<AuthResponse>('/auth/register/', data),
  refresh: (refresh: string) =>
    api.post<{ access: string; refresh: string }>('/auth/refresh/', { refresh }),
  logout: (refresh: string) => api.post('/auth/logout/', { refresh }),
  me: () => api.get('/auth/me/'),
}

export const transactionsApi = {
  list: (filters?: TransactionFilters) =>
    api.get<PaginatedResponse<Transaction>>('/transactions/', { params: filters }),
  get: (id: number) => api.get<Transaction>(`/transactions/${id}/`),
  update: (id: number, data: Partial<Transaction>) =>
    api.patch<Transaction>(`/transactions/${id}/update/`, data),
  delete: (id: number) => api.delete(`/transactions/${id}/delete/`),
  import: (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post<ImportBatch>('/transactions/import/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  importHistory: () => api.get<ImportBatch[]>('/transactions/import/history/'),
  importDetail: (id: number) => api.get<ImportBatch>(`/transactions/import/${id}/`),
}

export const categoriesApi = {
  list: () => api.get<Category[]>('/categories/'),
  create: (data: Partial<Category>) => api.post<Category>('/categories/create/', data),
  update: (id: number, data: Partial<Category>) =>
    api.patch<Category>(`/categories/${id}/update/`, data),
  delete: (id: number) => api.delete(`/categories/${id}/delete/`),
  rules: () => api.get<CategoryRule[]>('/categories/rules/'),
  createRule: (data: Partial<CategoryRule>) =>
    api.post<CategoryRule>('/categories/rules/create/', data),
  deleteRule: (id: number) => api.delete(`/categories/rules/${id}/delete/`),
}

export const budgetsApi = {
  list: (params?: { year?: number; month?: number }) => api.get<Budget[]>('/budgets/', { params }),
  create: (data: Partial<Budget>) => api.post<Budget>('/budgets/create/', data),
  update: (id: number, data: Partial<Budget>) => api.patch<Budget>(`/budgets/${id}/update/`, data),
  delete: (id: number) => api.delete(`/budgets/${id}/delete/`),
}

export const statsApi = {
  summary: (params?: Record<string, string>) =>
    api.get<StatsSummary>('/stats/summary/', { params }),
  byCategory: (params?: Record<string, string>) =>
    api.get<CategoryStats[]>('/stats/by-category/', { params }),
  monthly: (params?: Record<string, string>) =>
    api.get<MonthlyTrend[]>('/stats/monthly/', { params }),
  topMerchants: (params?: Record<string, string>) =>
    api.get<TopMerchant[]>('/stats/top-merchants/', { params }),
  balance: () => api.get<BalancePoint[]>('/stats/balance/'),
  comparison: (params?: Record<string, string>) =>
    api.get<CategoryComparison[]>('/stats/comparison/', { params }),
}

export const suggestionsApi = {
  list: () => api.get<Suggestion[]>('/suggestions/'),
}
