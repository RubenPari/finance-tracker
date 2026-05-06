<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { transactionsApi, categoriesApi } from '@/api'
import type { Transaction, Category } from '@/types'
import { formatCurrency, formatDate } from '@/utils/formatters'
import LoadingSpinner from '@/components/ui/LoadingSpinner.vue'
import EmptyState from '@/components/ui/EmptyState.vue'

const transactions = ref<Transaction[]>([])
const categories = ref<Category[]>([])
const totalCount = ref(0)
const loading = ref(true)
const page = ref(1)
const totalPages = ref(1)

const filters = ref({
  search: '',
  category: undefined as number | undefined,
  sign: undefined as 'expense' | 'income' | undefined,
  ordering: '-completed_at',
})

const editingId = ref<number | null>(null)
const editCategory = ref<number | null>(null)
const editNotes = ref('')

async function loadData() {
  loading.value = true
  try {
    const [txRes, catRes] = await Promise.all([
      transactionsApi.list({ ...filters.value, page: page.value }),
      categoriesApi.list(),
    ])
    transactions.value = txRes.data.results
    totalCount.value = txRes.data.count
    totalPages.value = Math.ceil(txRes.data.count / 50)
    categories.value = catRes.data
  } finally {
    loading.value = false
  }
}

function resetFilters() {
  filters.value.search = ''
  filters.value.category = undefined
  filters.value.sign = undefined
  page.value = 1
}

function startEdit(tx: Transaction) {
  editingId.value = tx.id
  editCategory.value = tx.category
  editNotes.value = tx.notes
}

async function saveEdit(tx: Transaction) {
  await transactionsApi.update(tx.id, {
    category: editCategory.value,
    notes: editNotes.value,
  })
  Object.assign(tx, { category: editCategory.value, notes: editNotes.value })
  editingId.value = null
}

function cancelEdit() {
  editingId.value = null
}

async function deleteTx(id: number) {
  if (!confirm('Eliminare questa transazione?')) return
  await transactionsApi.delete(id)
  transactions.value = transactions.value.filter((t) => t.id !== id)
}

onMounted(loadData)
watch([filters, page], loadData, { deep: true })
</script>

<template>
  <div>
    <div class="mb-6 flex flex-wrap items-center justify-between gap-4">
      <h1 class="text-2xl font-bold text-gray-900">Transazioni</h1>
      <span class="text-sm text-gray-500">{{ totalCount }} risultati</span>
    </div>

    <div class="card mb-6">
      <div class="grid grid-cols-1 gap-4 sm:grid-cols-4">
        <input
          v-model="filters.search"
          type="text"
          class="input-field"
          placeholder="Cerca per descrizione..."
        />
        <select v-model="filters.category" class="input-field">
          <option :value="undefined">Tutte le categorie</option>
          <option v-for="cat in categories" :key="cat.id" :value="cat.id">
            {{ cat.name }}
          </option>
        </select>
        <select v-model="filters.sign" class="input-field">
          <option :value="undefined">Tutti i tipi</option>
          <option value="expense">Solo spese</option>
          <option value="income">Solo entrate</option>
        </select>
        <button class="btn-secondary" @click="resetFilters">Azzera filtri</button>
      </div>
    </div>

    <LoadingSpinner v-if="loading" />
    <EmptyState v-else-if="!transactions.length" message="Nessuna transazione trovata" />
    <template v-else>
      <div class="card overflow-x-auto">
        <table class="w-full text-sm">
          <thead>
            <tr class="border-b border-gray-200 text-left text-xs uppercase text-gray-500">
              <th class="pb-3 pr-4">Data</th>
              <th class="pb-3 pr-4">Descrizione</th>
              <th class="pb-3 pr-4">Categoria</th>
              <th class="pb-3 pr-4 text-right">Importo</th>
              <th class="pb-3 pr-4">Azioni</th>
            </tr>
          </thead>
          <tbody>
            <template v-for="tx in transactions" :key="tx.id">
              <tr class="border-b border-gray-100 hover:bg-gray-50" :class="{
                'bg-blue-50/50': editingId === tx.id,
              }">
                <td class="py-3 pr-4 whitespace-nowrap text-gray-600">
                  {{ formatDate(tx.completed_at) }}
                </td>
                <td class="py-3 pr-4 max-w-xs truncate text-gray-900">
                  {{ tx.description }}
                </td>
                <td class="py-3 pr-4">
                  <template v-if="editingId === tx.id">
                    <select v-model="editCategory" class="input-field py-1 text-xs">
                      <option :value="null">Nessuna</option>
                      <option v-for="cat in categories" :key="cat.id" :value="cat.id">
                        {{ cat.name }}
                      </option>
                    </select>
                  </template>
                  <template v-else>
                    <span
                      v-if="tx.category_name"
                      class="inline-flex items-center gap-1 rounded-full px-2 py-0.5 text-xs font-medium"
                      :style="{
                        backgroundColor: `${tx.category_color ?? '#6B7280'}20`,
                        color: tx.category_color ?? '#6B7280',
                      }"
                    >
                      {{ tx.category_name }}
                    </span>
                    <span v-else class="text-xs text-gray-400">—</span>
                  </template>
                </td>
                <td class="py-3 pr-4 text-right font-medium whitespace-nowrap" :class="{
                  'text-red-600': tx.amount < 0,
                  'text-green-600': tx.amount > 0,
                  'text-gray-500': tx.amount === 0,
                }">
                  {{ formatCurrency(tx.amount) }}
                </td>
                <td class="py-3 pr-4 whitespace-nowrap">
                  <template v-if="editingId === tx.id">
                    <button class="btn-primary mr-1 px-2 py-1 text-xs" @click="saveEdit(tx)">
                      Salva
                    </button>
                    <button class="btn-secondary px-2 py-1 text-xs" @click="cancelEdit">
                      Annulla
                    </button>
                  </template>
                  <template v-else>
                    <button class="btn-secondary mr-1 px-2 py-1 text-xs" @click="startEdit(tx)">
                      Modifica
                    </button>
                    <button class="btn-danger px-2 py-1 text-xs" @click="deleteTx(tx.id)">
                      Elimina
                    </button>
                  </template>
                </td>
              </tr>
              <tr v-if="editingId === tx.id" class="border-b border-gray-100 bg-blue-50/30">
                <td colspan="5" class="px-4 py-2">
                  <label class="mb-1 block text-xs font-medium text-gray-600">Note</label>
                  <input
                    v-model="editNotes"
                    type="text"
                    class="input-field"
                    placeholder="Aggiungi note personali..."
                  />
                </td>
              </tr>
            </template>
          </tbody>
        </table>
      </div>

      <div v-if="totalPages > 1" class="mt-4 flex items-center justify-center gap-2">
        <button
          class="btn-secondary"
          :disabled="page <= 1"
          @click="page--"
        >
          Precedente
        </button>
        <span class="text-sm text-gray-500">
          Pagina {{ page }} di {{ totalPages }}
        </span>
        <button
          class="btn-secondary"
          :disabled="page >= totalPages"
          @click="page++"
        >
          Successiva
        </button>
      </div>
    </template>
  </div>
</template>
