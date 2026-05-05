<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const auth = useAuthStore()

const form = ref({
  email: '',
  password: '',
  password_confirm: '',
  first_name: '',
  last_name: '',
})
const error = ref('')
const fieldErrors = ref<Record<string, string[]>>({})
const loading = ref(false)

async function onSubmit() {
  error.value = ''
  fieldErrors.value = {}
  loading.value = true
  try {
    await auth.register(form.value)
    router.push('/dashboard')
  } catch (e: unknown) {
    const resp = (e as { response?: { data?: Record<string, unknown> } }).response
    if (resp?.data) {
      const data = resp.data as Record<string, unknown>
      if (data.password_confirm) fieldErrors.value.password_confirm = [data.password_confirm as string]
      if (data.email) fieldErrors.value.email = [data.email as string]
      if (data.password) fieldErrors.value.password = [data.password as string]
      if (data.detail) error.value = data.detail as string
      else error.value = 'Registrazione fallita. Controlla i dati inseriti.'
    }
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
          <h1 class="mt-3 text-2xl font-bold text-gray-900">Crea un account</h1>
          <p class="mt-1 text-sm text-gray-500">Inizia a tracciare le tue finanze</p>
        </div>

        <form class="space-y-4" @submit.prevent="onSubmit">
          <div v-if="error" class="rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">
            {{ error }}
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div>
              <label class="mb-1 block text-sm font-medium text-gray-700">Nome</label>
              <input v-model="form.first_name" type="text" class="input-field" placeholder="Mario" />
            </div>
            <div>
              <label class="mb-1 block text-sm font-medium text-gray-700">Cognome</label>
              <input v-model="form.last_name" type="text" class="input-field" placeholder="Rossi" />
            </div>
          </div>

          <div>
            <label class="mb-1 block text-sm font-medium text-gray-700">Email</label>
            <input
              v-model="form.email"
              type="email"
              required
              class="input-field"
              :class="{ 'border-red-500': fieldErrors.email }"
              placeholder="nome@email.com"
            />
            <p v-if="fieldErrors.email" class="mt-1 text-xs text-red-600">
              {{ fieldErrors.email[0] }}
            </p>
          </div>

          <div>
            <label class="mb-1 block text-sm font-medium text-gray-700">Password</label>
            <input
              v-model="form.password"
              type="password"
              required
              class="input-field"
              :class="{ 'border-red-500': fieldErrors.password }"
              placeholder="••••••••"
            />
            <p v-if="fieldErrors.password" class="mt-1 text-xs text-red-600">
              {{ fieldErrors.password[0] }}
            </p>
          </div>

          <div>
            <label class="mb-1 block text-sm font-medium text-gray-700">Conferma password</label>
            <input
              v-model="form.password_confirm"
              type="password"
              required
              class="input-field"
              :class="{ 'border-red-500': fieldErrors.password_confirm }"
              placeholder="••••••••"
            />
            <p v-if="fieldErrors.password_confirm" class="mt-1 text-xs text-red-600">
              {{ fieldErrors.password_confirm[0] }}
            </p>
          </div>

          <button type="submit" class="btn-primary w-full" :disabled="loading">
            {{ loading ? 'Registrazione...' : 'Registrati' }}
          </button>
        </form>

        <p class="mt-4 text-center text-sm text-gray-500">
          Hai già un account?
          <RouterLink to="/login" class="font-medium text-blue-600 hover:text-blue-500">
            Accedi
          </RouterLink>
        </p>
      </div>
    </div>
  </div>
</template>
