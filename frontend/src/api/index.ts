/**
 * API client configuration and all API endpoint functions.
 *
 * Uses Axios with two separate instances:
 * - `api`: The main client for authenticated requests. Includes a request
 *   interceptor that attaches the JWT access token, and a response interceptor
 *   that automatically refreshes expired tokens using the refresh token.
 * - `refreshClient`: A dedicated client for token refresh calls to avoid
 *   recursive interceptor loops.
 *
 * All endpoints are grouped by domain (auth, transactions, categories,
 * budgets, stats, suggestions) and return typed responses.
 */
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

/** Base API client for authenticated requests. */
const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
})

/** Dedicated client for token refresh (avoids recursive interceptor loops). */
const refreshClient = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
})

/**
 * Request interceptor: attach the JWT access token to every outgoing request.
 * Reads the current token from the Pinia auth store.
 */
api.interceptors.request.use((config) => {
  const store = useAuthStore()
  if (store.accessToken) {
    config.headers.Authorization = `Bearer ${store.accessToken}`
  }
  return config
})

/**
 * Response interceptor: handle 401 Unauthorized errors by attempting
 * an automatic token refresh. If the refresh fails, logs the user out
 * and redirects to the login page.
 */
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const store = useAuthStore()
    const original = error.config

    // Only attempt refresh for 401 errors that haven't already been retried
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

/**
 * Authentication API endpoints.
 * Covers login, registration, token refresh, logout, and current user fetch.
 */
export const authApi = {
  /** POST /auth/login/ - Authenticate with email and password. */
  login: (email: string, password: string) =>
    api.post<AuthResponse>('/auth/login/', { email, password }),
  /** POST /auth/register/ - Create a new user account. */
  register: (data: Record<string, string>) => api.post<AuthResponse>('/auth/register/', data),
  /** POST /auth/refresh/ - Exchange a refresh token for new access/refresh tokens. */
  refresh: (refresh: string) =>
    api.post<{ access: string; refresh: string }>('/auth/refresh/', { refresh }),
  /** POST /auth/logout/ - Blacklist the refresh token and invalidate the session. */
  logout: (refresh: string) => api.post('/auth/logout/', { refresh }),
  /** GET /auth/me/ - Fetch the current authenticated user's profile. */
  me: () => api.get('/auth/me/'),
}

/**
 * Transactions API endpoints.
 * Covers CRUD operations, file import, and import history/detail queries.
 */
export const transactionsApi = {
  /** GET /transactions/ - List transactions with optional filters and pagination. */
  list: (filters?: TransactionFilters) =>
    api.get<PaginatedResponse<Transaction>>('/transactions/', { params: filters }),
  /** GET /transactions/:id - Fetch a single transaction by ID. */
  get: (id: number) => api.get<Transaction>(`/transactions/${id}/`),
  /** PATCH /transactions/:id/update - Partially update a transaction. */
  update: (id: number, data: Partial<Transaction>) =>
    api.patch<Transaction>(`/transactions/${id}/update/`, data),
  /** DELETE /transactions/:id/delete - Delete a transaction. */
  delete: (id: number) => api.delete(`/transactions/${id}/delete/`),
  /** POST /transactions/import/ - Upload an XLSX file for async import processing. */
  import: (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post<ImportBatch>('/transactions/import/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  /** GET /transactions/import/history/ - List all past import batches. */
  importHistory: () => api.get<ImportBatch[]>('/transactions/import/history/'),
  /** GET /transactions/import/:id - Fetch details of a specific import batch. */
  importDetail: (id: number) => api.get<ImportBatch>(`/transactions/import/${id}/`),
  /** GET /transactions/import/:id/transactions/ - List transactions from a specific import batch. */
  batchTransactions: (batchId: number, filters?: TransactionFilters) =>
    api.get<PaginatedResponse<Transaction>>(`/transactions/import/${batchId}/transactions/`, { params: filters }),
}

/**
 * Categories API endpoints.
 * Covers CRUD for categories and management of keyword-based categorization rules.
 */
export const categoriesApi = {
  /** GET /categories/ - List all categories (system and user-created). */
  list: () => api.get<Category[]>('/categories/'),
  /** POST /categories/create/ - Create a new user category. */
  create: (data: Partial<Category>) => api.post<Category>('/categories/create/', data),
  /** PATCH /categories/:id/update - Update a user category. */
  update: (id: number, data: Partial<Category>) =>
    api.patch<Category>(`/categories/${id}/update/`, data),
  /** DELETE /categories/:id/delete - Delete a user category. */
  delete: (id: number) => api.delete(`/categories/${id}/delete/`),
  /** GET /categories/rules/ - List all keyword-based categorization rules. */
  rules: () => api.get<CategoryRule[]>('/categories/rules/'),
  /** POST /categories/rules/create/ - Create a new categorization rule. */
  createRule: (data: Partial<CategoryRule>) =>
    api.post<CategoryRule>('/categories/rules/create/', data),
  /** DELETE /categories/rules/:id/delete - Delete a categorization rule. */
  deleteRule: (id: number) => api.delete(`/categories/rules/${id}/delete/`),
}

/**
 * Budgets API endpoints.
 * Covers CRUD for monthly category budgets with optional year/month filtering.
 */
export const budgetsApi = {
  /** GET /budgets/ - List budgets, optionally filtered by year and month. */
  list: (params?: { year?: number; month?: number }) => api.get<Budget[]>('/budgets/', { params }),
  /** POST /budgets/create/ - Create a new budget. */
  create: (data: Partial<Budget>) => api.post<Budget>('/budgets/create/', data),
  /** PATCH /budgets/:id/update - Update a budget's limit. */
  update: (id: number, data: Partial<Budget>) => api.patch<Budget>(`/budgets/${id}/update/`, data),
  /** DELETE /budgets/:id/delete - Delete a budget. */
  delete: (id: number) => api.delete(`/budgets/${id}/delete/`),
}

/**
 * Statistics API endpoints.
 * Covers summary, category breakdown, monthly trends, top merchants,
 * running balance, and period-over-period comparisons.
 */
export const statsApi = {
  /** GET /stats/summary/ - Get income, expenses, net, and transaction count for a period. */
  summary: (params?: Record<string, string>) =>
    api.get<StatsSummary>('/stats/summary/', { params }),
  /** GET /stats/by-category/ - Get spending totals grouped by category. */
  byCategory: (params?: Record<string, string>) =>
    api.get<CategoryStats[]>('/stats/by-category/', { params }),
  /** GET /stats/monthly/ - Get monthly income/expense trends. */
  monthly: (params?: Record<string, string>) =>
    api.get<MonthlyTrend[]>('/stats/monthly/', { params }),
  /** GET /stats/top-merchants/ - Get top merchants by spending amount. */
  topMerchants: (params?: Record<string, string>) =>
    api.get<TopMerchant[]>('/stats/top-merchants/', { params }),
  /** GET /stats/balance/ - Get running balance history points. */
  balance: () => api.get<BalancePoint[]>('/stats/balance/'),
  /** GET /stats/comparison/ - Get category spending comparison between two periods. */
  comparison: (params?: Record<string, string>) =>
    api.get<CategoryComparison[]>('/stats/comparison/', { params }),
}

/**
 * Suggestions API endpoints.
 * Covers fetching AI-generated spending insights and anomaly detections.
 */
export const suggestionsApi = {
  /** GET /suggestions/ - List all AI-generated suggestions for the current user. */
  list: () => api.get<Suggestion[]>('/suggestions/'),
}
