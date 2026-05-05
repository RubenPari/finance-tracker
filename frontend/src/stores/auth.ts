import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { authApi } from '@/api'
import type { User } from '@/types'

export const useAuthStore = defineStore('auth', () => {
  const user = ref<User | null>(null)
  const accessToken = ref<string | null>(localStorage.getItem('access_token'))
  const refreshToken = ref<string | null>(localStorage.getItem('refresh_token'))

  const isAuthenticated = computed(() => !!accessToken.value)

  function setTokens(access: string, refresh: string) {
    accessToken.value = access
    refreshToken.value = refresh
    localStorage.setItem('access_token', access)
    localStorage.setItem('refresh_token', refresh)
  }

  function setUser(u: User) {
    user.value = u
  }

  async function login(email: string, password: string) {
    const { data } = await authApi.login(email, password)
    setTokens(data.access, data.refresh)
    setUser(data.user)
  }

  async function register(form: Record<string, string>) {
    const { data } = await authApi.register(form)
    setTokens(data.access, data.refresh)
    setUser(data.user)
  }

  async function fetchUser() {
    const { data } = await authApi.me()
    setUser(data)
  }

  function logout() {
    const token = refreshToken.value
    user.value = null
    accessToken.value = null
    refreshToken.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    if (token) {
      authApi.logout(token).catch(() => {})
    }
  }

  return {
    user,
    accessToken,
    refreshToken,
    isAuthenticated,
    login,
    register,
    logout,
    fetchUser,
    setTokens,
  }
})
