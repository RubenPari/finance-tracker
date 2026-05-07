<script setup lang="ts">
/**
 * TransactionsView - Displays a paginated, filterable list of transactions.
 *
 * Features:
 * - Filter by search text, category, and sign (income/expense)
 * - Inline editing of category and notes per transaction
 * - Deletion with confirmation dialog
 * - Pagination (50 items per page)
 *
 * Loads transactions and categories in parallel on mount.
 * Re-fetches whenever filters or page number change (deep watch on filters).
 */
import { ref, onMounted, watch } from 'vue'
import { transactionsApi, categoriesApi } from '@/api'
import type { Transaction, Category } from '@/types'
import { formatCurrency, formatDate } from '@/utils/formatters'
import { Card, CardContent } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  AlertDialog,
  AlertDialogAction,
  AlertDialogCancel,
  AlertDialogContent,
  AlertDialogDescription,
  AlertDialogFooter,
  AlertDialogHeader,
  AlertDialogTitle,
  AlertDialogTrigger,
} from '@/components/ui/alert-dialog'
import { Search, Pencil, Trash2, X, RotateCw, ArrowUp, ArrowDown, ArrowUpDown } from 'lucide-vue-next'

/** List of transactions for the current page */
const transactions = ref<Transaction[]>([])
/** All categories, used for filter dropdown and inline edit select */
const categories = ref<Category[]>([])
/** Total number of transactions matching the current filters */
const totalCount = ref(0)
/** Loading state for data fetching */
const loading = ref(true)
/** Current page number (1-indexed) */
const page = ref(1)
/** Total number of pages, calculated from totalCount / 50 items per page */
const totalPages = ref(1)

/** Active filters applied to the transaction list API call */
const filters = ref({
  search: '',
  category: undefined as number | undefined,
  sign: undefined as 'expense' | 'income' | undefined,
  ordering: '-completed_at',
})

/** ID of the transaction currently being edited inline, or null if none */
const editingId = ref<number | null>(null)
/** Selected category ID for the inline edit form */
const editCategory = ref<number | null>(null)
/** Notes text for the inline edit form */
const editNotes = ref('')

/**
 * Fetches the paginated, filtered transaction list and the full category list in parallel.
 * Calculates total pages from the response count (50 items per page).
 */
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

/** Resets all filters to defaults and returns to page 1. */
function resetFilters() {
  filters.value.search = ''
  filters.value.category = undefined
  filters.value.sign = undefined
  page.value = 1
}

/** Enters inline edit mode for a transaction, populating the edit form with its current values. */
function startEdit(tx: Transaction) {
  editingId.value = tx.id
  editCategory.value = tx.category
  editNotes.value = tx.notes
}

/**
 * Saves the edited category and notes to the backend via the transactions API.
 * On success, mutates the transaction object in-place using Object.assign to update the reactive array,
 * then exits edit mode.
 */
async function saveEdit(tx: Transaction) {
  await transactionsApi.update(tx.id, {
    category: editCategory.value,
    notes: editNotes.value,
  })
  Object.assign(tx, { category: editCategory.value, notes: editNotes.value })
  editingId.value = null
}

/** Exits inline edit mode without saving changes. */
function cancelEdit() {
  editingId.value = null
}

/** Sortable columns mapped to their backend ordering field. */
const sortableColumns: { key: string; label: string; field: string; align?: 'right' }[] = [
  { key: 'date', label: 'Data', field: 'completed_at' },
  { key: 'description', label: 'Descrizione', field: 'description' },
  { key: 'category', label: 'Categoria', field: 'category__name' },
  { key: 'amount', label: 'Importo', field: 'amount', align: 'right' },
]

/** Fields whose default sort direction is descending (numeric/date columns). */
const descFirstFields = new Set(['completed_at', 'amount'])

/**
 * Toggles the sort order on a column.
 * - If the column is already the active ordering, flips asc/desc.
 * - Otherwise sets the column's natural default direction (desc for date/amount, asc for text).
 * Always resets to page 1 so the user sees the top of the new ordering.
 */
function toggleSort(field: string) {
  const current = filters.value.ordering
  if (current === field) {
    filters.value.ordering = `-${field}`
  } else if (current === `-${field}`) {
    filters.value.ordering = field
  } else {
    filters.value.ordering = descFirstFields.has(field) ? `-${field}` : field
  }
  page.value = 1
}

/** Returns the current sort direction for a column: 'asc', 'desc', or null. */
function sortDirection(field: string): 'asc' | 'desc' | null {
  if (filters.value.ordering === field) return 'asc'
  if (filters.value.ordering === `-${field}`) return 'desc'
  return null
}

/**
 * Deletes a transaction by ID from the backend.
 * On success, removes it from the local reactive array (no re-fetch needed).
 */
async function deleteTx(id: number) {
  await transactionsApi.delete(id)
  transactions.value = transactions.value.filter((t) => t.id !== id)
}

// Fetch data on initial mount
onMounted(loadData)
// Re-fetch whenever filters or page change; deep: true ensures nested filter changes trigger the watch
watch([filters, page], loadData, { deep: true })
</script>

<template>
  <div>
    <div class="mb-6 flex flex-wrap items-center justify-between gap-4">
      <h1 class="text-2xl font-bold tracking-tight">Transazioni</h1>
      <span class="text-sm text-muted-foreground">{{ totalCount }} risultati</span>
    </div>

    <Card class="mb-6">
      <CardContent class="pt-6">
        <div class="grid grid-cols-1 gap-4 sm:grid-cols-4">
          <div class="relative">
            <Search class="absolute left-3 top-1/2 size-4 -translate-y-1/2 text-muted-foreground" />
            <Input
              v-model="filters.search"
              type="text"
              placeholder="Cerca per descrizione..."
              class="pl-9"
            />
          </div>
          <Select
            :model-value="filters.category !== undefined ? String(filters.category) : ''"
            @update:model-value="filters.category = $event ? Number($event) : undefined"
          >
            <SelectTrigger>
              <SelectValue placeholder="Tutte le categorie" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem v-for="cat in categories" :key="cat.id" :value="String(cat.id)">
                {{ cat.name }}
              </SelectItem>
            </SelectContent>
          </Select>
          <Select
            :model-value="filters.sign ?? ''"
            @update:model-value="
              filters.sign = ($event || undefined) as 'expense' | 'income' | undefined
            "
          >
            <SelectTrigger>
              <SelectValue placeholder="Tutti i tipi" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="expense">Solo spese</SelectItem>
              <SelectItem value="income">Solo entrate</SelectItem>
            </SelectContent>
          </Select>
          <Button variant="outline" @click="resetFilters">
            <RotateCw class="mr-2 size-4" />
            Azzera filtri
          </Button>
        </div>
      </CardContent>
    </Card>

    <template v-if="loading">
      <div class="space-y-3">
        <Skeleton v-for="i in 5" :key="i" class="h-12" />
      </div>
    </template>
    <template v-else-if="!transactions.length">
      <Card>
        <CardContent class="py-12 text-center">
          <p class="text-muted-foreground">Nessuna transazione trovata</p>
        </CardContent>
      </Card>
    </template>
    <template v-else>
      <Card>
        <CardContent class="p-0">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead
                  v-for="col in sortableColumns"
                  :key="col.key"
                  :class="[
                    'cursor-pointer select-none hover:bg-muted/50 transition-colors',
                    col.align === 'right' ? 'text-right' : '',
                  ]"
                  @click="toggleSort(col.field)"
                >
                  <span
                    :class="[
                      'inline-flex items-center gap-1',
                      col.align === 'right' ? 'justify-end w-full' : '',
                    ]"
                  >
                    {{ col.label }}
                    <ArrowUp v-if="sortDirection(col.field) === 'asc'" class="size-3.5" />
                    <ArrowDown v-else-if="sortDirection(col.field) === 'desc'" class="size-3.5" />
                    <ArrowUpDown v-else class="size-3.5 text-muted-foreground/50" />
                  </span>
                </TableHead>
                <TableHead class="w-24">Azioni</TableHead>
              </TableRow>
            </TableHeader>
            <TableBody>
              <template v-for="tx in transactions" :key="tx.id">
                <TableRow :class="{ 'bg-muted/50': editingId === tx.id }">
                  <TableCell class="whitespace-nowrap text-muted-foreground">
                    {{ formatDate(tx.completed_at) }}
                  </TableCell>
                  <TableCell class="max-w-xs truncate font-medium">
                    {{ tx.description }}
                  </TableCell>
                  <TableCell>
                    <template v-if="editingId === tx.id">
                      <Select v-model="editCategory">
                        <SelectTrigger class="h-8 text-xs">
                          <SelectValue placeholder="Nessuna" />
                        </SelectTrigger>
                        <SelectContent>
                          <SelectItem :value="null">Nessuna</SelectItem>
                          <SelectItem v-for="cat in categories" :key="cat.id" :value="cat.id">
                            {{ cat.name }}
                          </SelectItem>
                        </SelectContent>
                      </Select>
                    </template>
                    <template v-else>
                      <Badge
                        v-if="tx.category_name"
                        :style="{
                          backgroundColor: `${tx.category_color ?? '#6B7280'}20`,
                          color: tx.category_color ?? '#6B7280',
                        }"
                        variant="secondary"
                      >
                        {{ tx.category_name }}
                      </Badge>
                      <span v-else class="text-muted-foreground">—</span>
                    </template>
                  </TableCell>
                  <TableCell
                    class="whitespace-nowrap text-right font-mono tabular-nums font-medium"
                    :class="{
                      'text-expense': tx.amount < 0,
                      'text-income': tx.amount > 0,
                      'text-muted-foreground': tx.amount === 0,
                    }"
                  >
                    {{ formatCurrency(tx.amount) }}
                  </TableCell>
                  <TableCell>
                    <div class="flex items-center gap-1">
                      <template v-if="editingId === tx.id">
                        <Button size="sm" @click="saveEdit(tx)">Salva</Button>
                        <Button size="sm" variant="outline" @click="cancelEdit">Annulla</Button>
                      </template>
                      <template v-else>
                        <Button size="icon" variant="ghost" @click="startEdit(tx)">
                          <Pencil class="size-4" />
                        </Button>
                        <AlertDialog>
                          <AlertDialogTrigger as-child>
                            <Button
                              size="icon"
                              variant="ghost"
                              class="text-destructive hover:text-destructive"
                            >
                              <Trash2 class="size-4" />
                            </Button>
                          </AlertDialogTrigger>
                          <AlertDialogContent>
                            <AlertDialogHeader>
                              <AlertDialogTitle>Eliminare la transazione?</AlertDialogTitle>
                              <AlertDialogDescription>
                                Questa azione non può essere annullata. La transazione verrà
                                eliminata definitivamente.
                              </AlertDialogDescription>
                            </AlertDialogHeader>
                            <AlertDialogFooter>
                              <AlertDialogCancel>Annulla</AlertDialogCancel>
                              <AlertDialogAction
                                class="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                                @click="deleteTx(tx.id)"
                              >
                                Elimina
                              </AlertDialogAction>
                            </AlertDialogFooter>
                          </AlertDialogContent>
                        </AlertDialog>
                      </template>
                    </div>
                  </TableCell>
                </TableRow>
                <TableRow v-if="editingId === tx.id" class="bg-muted/30">
                  <TableCell colspan="5" class="px-6 py-2">
                    <div class="space-y-1">
                      <label class="text-xs font-medium text-muted-foreground">Note</label>
                      <Input
                        v-model="editNotes"
                        type="text"
                        placeholder="Aggiungi note personali..."
                      />
                    </div>
                  </TableCell>
                </TableRow>
              </template>
            </TableBody>
          </Table>
        </CardContent>
      </Card>

      <div v-if="totalPages > 1" class="mt-4 flex items-center justify-center gap-2">
        <Button variant="outline" size="sm" :disabled="page <= 1" @click="page--">
          Precedente
        </Button>
        <span class="text-sm text-muted-foreground"> Pagina {{ page }} di {{ totalPages }} </span>
        <Button variant="outline" size="sm" :disabled="page >= totalPages" @click="page++">
          Successiva
        </Button>
      </div>
    </template>
  </div>
</template>
