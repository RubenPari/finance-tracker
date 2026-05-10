import axios from 'axios'
import type { AxiosError, InternalAxiosRequestConfig } from 'axios'
import { useAuthStore } from '@/stores/auth'

type RetryableRequestConfig = InternalAxiosRequestConfig & { _retry?: boolean }

/** Base API client for authenticated requests. */
export const api = axios.create({
  baseURL: '/api',
  headers: { 'Content-Type': 'application/json' },
})

/** Dedicated client for token refresh (avoids recursive interceptor loops). */
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
  async (error: AxiosError) => {
    const store = useAuthStore()
    const original = error.config as RetryableRequestConfig | undefined

    if (error.response?.status === 401 && original && !original._retry && store.refreshToken) {
      original._retry = true
      try {
        const { data } = await refreshClient.post<{ access: string; refresh: string }>('/auth/refresh/', {
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
