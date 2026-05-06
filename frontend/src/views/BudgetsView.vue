<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { budgetsApi, categoriesApi } from '@/api'
import type { Budget, Category } from '@/types'
import { formatCurrency } from '@/utils/formatters'
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'
import EmptyState from '@/components/ui/EmptyState.vue'

const budgets = ref<Budget[]>([])
const categories = ref<Category[]>([])
const loading = ref(true)
const year = ref(new Date().getFullYear())
const month = ref(new Date().getMonth() + 1)

const showCreate = ref(false)
const newBudget = ref({
  category: null as number | null,
  amount_limit: 0,
})

async function loadData() {
  loading.value = true
  try {
    const [bRes, cRes] = await Promise.all([
      budgetsApi.list({ year: year.value, month: month.value }),
      categoriesApi.list(),
    ])
    budgets.value = bRes.data
    categories.value = cRes.data
  } finally {
    loading.value = false
  }
}

async function createBudget() {
  if (!newBudget.value.category || newBudget.value.amount_limit <= 0) return
  await budgetsApi.create({
    category: newBudget.value.category,
    year: year.value,
    month: month.value,
    amount_limit: newBudget.value.amount_limit,
  })
  newBudget.value = { category: null, amount_limit: 0 }
  showCreate.value = false
  await loadData()
}

async function deleteBudget(id: number) {
  await budgetsApi.delete(id)
  await loadData()
}

const months = [
  'Gennaio',
  'Febbraio',
  'Marzo',
  'Aprile',
  'Maggio',
  'Giugno',
  'Luglio',
  'Agosto',
  'Settembre',
  'Ottobre',
  'Novembre',
  'Dicembre',
]

function prevMonth() {
  if (month.value === 1) {
    month.value = 12
    year.value--
  } else {
    month.value--
  }
}

function nextMonth() {
  if (month.value === 12) {
    month.value = 1
    year.value++
  } else {
    month.value++
  }
}

onMounted(loadData)
</script>

<template>
  <div>
    <div class="mb-6 flex flex-wrap items-center justify-between gap-4">
      <h1 class="text-2xl font-bold text-gray-900">Budget</h1>
      <button class="btn-primary" @click="showCreate = !showCreate">+ Nuovo budget</button>
    </div>

    <div class="card mb-6">
      <div class="flex items-center justify-between">
        <button class="btn-secondary text-sm" @click="prevMonth">◀</button>
        <span class="text-lg font-semibold text-gray-900">
          {{ months[month - 1] }} {{ year }}
        </span>
        <button class="btn-secondary text-sm" @click="nextMonth">▶</button>
      </div>
    </div>

    <div v-if="showCreate" class="card mb-6">
      <div class="flex items-end gap-3">
        <div class="flex-1">
          <label class="mb-1 block text-xs font-medium text-gray-600">Categoria</label>
          <select v-model="newBudget.category" class="input-field">
            <option :value="null">Seleziona...</option>
            <option v-for="cat in categories" :key="cat.id" :value="cat.id">
              {{ cat.name }}
            </option>
          </select>
        </div>
        <div>
          <label class="mb-1 block text-xs font-medium text-gray-600">Limite (€)</label>
          <input
            v-model.number="newBudget.amount_limit"
            type="number"
            min="0"
            step="1"
            class="input-field w-32"
          />
        </div>
        <button class="btn-primary" @click="createBudget">Crea</button>
        <button class="btn-secondary" @click="showCreate = false">Annulla</button>
      </div>
    </div>

    <LoadingSpinner v-if="loading" />
    <EmptyState v-else-if="!budgets.length" message="Nessun budget definito per questo mese" />
    <div v-else class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <div v-for="b in budgets" :key="b.id" class="card">
        <div class="mb-3 flex items-center justify-between">
          <div class="flex items-center gap-2">
            <span class="h-3 w-3 rounded-full" :style="{ backgroundColor: b.category_color }" />
            <span class="text-sm font-semibold text-gray-900">{{ b.category_name }}</span>
          </div>
          <button class="text-xs text-red-500 hover:text-red-700" @click="deleteBudget(b.id)">
            Elimina
          </button>
        </div>

        <div class="mb-2">
          <div class="flex justify-between text-sm">
            <span class="text-gray-600">{{ formatCurrency(b.current_spent) }}</span>
            <span class="text-gray-400">{{ formatCurrency(b.amount_limit) }}</span>
          </div>
          <div class="mt-1 h-2.5 w-full overflow-hidden rounded-full bg-gray-200">
            <div
              class="h-full rounded-full transition-all duration-300"
              :class="{
                'bg-green-500': b.percentage < 80,
                'bg-yellow-500': b.percentage >= 80 && b.percentage < 100,
                'bg-red-500': b.percentage >= 100,
              }"
              :style="{ width: `${Math.min(b.percentage, 100)}%` }"
            />
          </div>
        </div>

        <div class="flex items-center justify-between text-xs">
          <span class="text-gray-400">{{ b.percentage }}% utilizzato</span>
          <span v-if="b.percentage >= 100" class="font-medium text-red-600">Budget superato!</span>
          <span v-else-if="b.percentage >= 80" class="font-medium text-yellow-600">Attenzione</span>
          <span v-else class="font-medium text-green-600">
            {{ formatCurrency(b.amount_limit - b.current_spent) }} rimanenti
          </span>
        </div>
      </div>
    </div>
  </div>
</template>
