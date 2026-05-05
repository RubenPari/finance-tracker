<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()

const email = ref('')
const password = ref('')
const error = ref('')
const loading = ref(false)

async function onSubmit() {
  error.value = ''
  loading.value = true
  try {
    await auth.login(email.value, password.value)
    router.push('/dashboard')
  } catch {
    error.value = 'Email o password non validi.'
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="flex min-h-screen items-center justify-center bg-gray-50 px-4">
    <div class="w-full max-w-md">
      <div class="card">
        <div class="mb-8 text-center">
          <span class="text-4xl">📊</span>
          <h1 class="mt-3 text-2xl font-bold text-gray-900">Finance Tracker</h1>
          <p class="mt-1 text-sm text-gray-500">Accedi al tuo account</p>
        </div>

        <form class="space-y-4" @submit.prevent="onSubmit">
          <div v-if="error" class="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">
            {{ error }}
          </div>

          <div>
            <label class="mb-1 block text-sm font-medium text-gray-700">Email</label>
            <input
              v-model="email"
              type="email"
              required
              class="input-field"
              placeholder="nome@email.com"
              autocomplete="email"
            />
          </div>

          <div>
            <label class="mb-1 block text-sm font-medium text-gray-700">Password</label>
            <input
              v-model="password"
              type="password"
              required
              class="input-field"
              placeholder="••••••••"
              autocomplete="current-password"
            />
          </div>

          <button type="submit" class="btn-primary w-full" :disabled="loading">
            {{ loading ? 'Accesso in corso...' : 'Accedi' }}
          </button>
        </form>

        <p class="mt-4 text-center text-sm text-gray-500">
          Non hai un account?
          <RouterLink to="/register" class="font-medium text-blue-600 hover:text-blue-500">
            Registrati
          </RouterLink>
        </p>
      </div>
    </div>
  </div>
</template>
