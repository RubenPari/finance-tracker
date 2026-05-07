<script setup lang="ts">
/**
 * RegisterView - User registration page.
 *
 * Displays a registration form with first name, last name, email, password, and password confirmation.
 * On submit, calls the auth store's register method and redirects to the dashboard on success.
 *
 * Error handling:
 * - `error` displays a general error message (e.g., backend `detail` field or generic failure)
 * - `fieldErrors` maps field names to arrays of validation error messages from the backend
 *   (e.g., password mismatch, duplicate email, weak password)
 */
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import AuthLayout from '@/components/layout/AuthLayout.vue'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Button } from '@/components/ui/button'

const router = useRouter()
const auth = useAuthStore()

/** Registration form data: email, password, confirmation, and optional name fields */
const form = ref({
  email: '',
  password: '',
  password_confirm: '',
  first_name: '',
  last_name: '',
})
/** General error message shown for non-field-specific errors (e.g., server detail message) */
const error = ref('')
/** Per-field validation errors from the backend, keyed by field name with arrays of messages */
const fieldErrors = ref<Record<string, string[]>>({})
/** Loading state to disable the submit button during the API call */
const loading = ref(false)

/**
 * Handles form submission.
 * Calls the auth store register method with the form data.
 * On success, navigates to the dashboard. On failure, parses the error response:
 * - Extracts field-specific errors (password_confirm, email, password) into fieldErrors for inline display
 * - Uses the backend `detail` message if available, otherwise shows a generic failure message
 * The loading state prevents double submissions and provides visual feedback.
 */
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
      if (data.password_confirm)
        fieldErrors.value.password_confirm = [data.password_confirm as string]
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
  <AuthLayout>
    <Card class="w-full max-w-md">
      <CardHeader class="text-center">
        <CardTitle class="text-2xl">Crea un account</CardTitle>
        <CardDescription>Inizia a tracciare le tue finanze</CardDescription>
      </CardHeader>
      <CardContent>
        <form class="space-y-4" @submit.prevent="onSubmit">
          <div
            v-if="error"
            class="rounded-lg border border-destructive/50 bg-destructive/10 px-4 py-3 text-sm text-destructive"
          >
            {{ error }}
          </div>

          <div class="grid grid-cols-2 gap-4">
            <div class="space-y-2">
              <Label for="first_name">Nome</Label>
              <Input id="first_name" v-model="form.first_name" type="text" placeholder="Mario" />
            </div>
            <div class="space-y-2">
              <Label for="last_name">Cognome</Label>
              <Input id="last_name" v-model="form.last_name" type="text" placeholder="Rossi" />
            </div>
          </div>

          <div class="space-y-2">
            <Label for="email">Email</Label>
            <Input
              id="email"
              v-model="form.email"
              type="email"
              required
              placeholder="nome@email.com"
            />
            <p v-if="fieldErrors.email" class="text-xs text-destructive">
              {{ fieldErrors.email[0] }}
            </p>
          </div>

          <div class="space-y-2">
            <Label for="password">Password</Label>
            <Input
              id="password"
              v-model="form.password"
              type="password"
              required
              placeholder="••••••••"
            />
            <p v-if="fieldErrors.password" class="text-xs text-destructive">
              {{ fieldErrors.password[0] }}
            </p>
          </div>

          <div class="space-y-2">
            <Label for="password_confirm">Conferma password</Label>
            <Input
              id="password_confirm"
              v-model="form.password_confirm"
              type="password"
              required
              placeholder="••••••••"
            />
            <p v-if="fieldErrors.password_confirm" class="text-xs text-destructive">
              {{ fieldErrors.password_confirm[0] }}
            </p>
          </div>

          <Button type="submit" class="w-full" :disabled="loading">
            {{ loading ? 'Registrazione...' : 'Registrati' }}
          </Button>
        </form>

        <p class="mt-4 text-center text-sm text-muted-foreground">
          Hai già un account?
          <RouterLink to="/login" class="font-medium text-primary hover:underline">
            Accedi
          </RouterLink>
        </p>
      </CardContent>
    </Card>
  </AuthLayout>
</template>