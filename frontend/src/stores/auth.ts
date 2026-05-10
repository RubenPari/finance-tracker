/**
 * Pinia authentication store.
 *
 * Manages the authenticated user session, including JWT access/refresh
 * tokens (persisted in localStorage), login/register/logout flows,
 * and automatic user profile fetching.
 *
 * The store is consumed by the API client's request interceptor for
 * token attachment and by the router's navigation guard for access control.
 */
import { ref, computed } from 'vue'
import { defineStore } from 'pinia'
import { authApi } from '@/api'
import type { User } from '@/types'

export const useAuthStore = defineStore('auth', () => {
  /** Currently authenticated user profile, or null if unauthenticated. */
  const user = ref<User | null>(null)

  /** JWT access token, restored from localStorage on app load. */
  const accessToken = ref<string | null>(localStorage.getItem('access_token'))

  /** JWT refresh token, restored from localStorage on app load. */
  const refreshToken = ref<string | null>(localStorage.getItem('refresh_token'))

  /** Derived boolean indicating whether the user has a valid access token. */
  const isAuthenticated = computed(() => !!accessToken.value)

  /**
   * Store new access and refresh tokens, persisting both to localStorage.
   *
   * @param access - JWT access token.
   * @param refresh - JWT refresh token.
   */
  function setTokens(access: string, refresh: string) {
    accessToken.value = access
    refreshToken.value = refresh
    localStorage.setItem('access_token', access)
    localStorage.setItem('refresh_token', refresh)
  }

  /**
   * Set the current user profile in the store.
   *
   * @param u - User object returned from the API.
   */
  function setUser(u: User) {
    user.value = u
  }

  /**
   * Authenticate the user with email and password.
   * Stores the returned tokens and user profile.
   *
   * @param email - User's email address.
   * @param password - User's password.
   */
  async function login(email: string, password: string) {
    const { data } = await authApi.login(email, password)
    setTokens(data.access, data.refresh)
    try {
      await fetchUser()
    } catch {
      logout()
      throw new Error('Impossibile recuperare il profilo utente dopo il login.')
    }
  }

  /**
   * Register a new user account and immediately authenticate.
   * Stores the returned tokens and user profile.
   *
   * @param form - Registration form fields (email, password, first_name, last_name).
   */
  async function register(form: Record<string, string>) {
    const { data } = await authApi.register(form)
    setTokens(data.access, data.refresh)
    setUser(data.user)
  }

  /**
   * Fetch the current user's profile from the /auth/me/ endpoint.
   * Called by the router guard on first navigation to hydrate the user state.
   */
  async function fetchUser() {
    const { data } = await authApi.me()
    setUser(data)
  }

  /**
   * Log the user out: clear local state, remove tokens from localStorage,
   * and asynchronously blacklist the refresh token on the server.
   */
  function logout() {
    const token = refreshToken.value
    user.value = null
    accessToken.value = null
    refreshToken.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    if (token) {
      // Best-effort server-side token blacklist (ignore failures)
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
