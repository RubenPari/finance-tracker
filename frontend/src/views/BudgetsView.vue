<script setup lang="ts">
/**
 * BudgetsView - Displays and manages monthly spending budgets per category.
 *
 * Features:
 * - Month/year navigation with prev/next buttons
 * - Budget cards showing spent vs. limit with progress bars
 * - Color-coded progress states: default (<80%), warning (80-99%), destructive (100%+)
 * - Create new budgets via dialog (category + amount limit)
 * - Delete budgets with confirmation dialog
 *
 * Fetches budgets for the selected year/month and all categories in parallel on mount.
 * Re-fetches whenever year or month changes.
 */
import { ref, onMounted, watch } from 'vue'
import { budgetsApi, categoriesApi } from '@/api'
import type { Budget, Category } from '@/types'
import { formatCurrency } from '@/utils/formatters'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
import { Badge } from '@/components/ui/badge'
import { Progress } from '@/components/ui/progress'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select'
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog'
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
import { Plus, ChevronLeft, ChevronRight, Trash2 } from 'lucide-vue-next'

/** List of budgets for the currently selected month/year */
const budgets = ref<Budget[]>([])
/** All categories, used for the create budget dialog dropdown */
const categories = ref<Category[]>([])
/** Loading state for data fetching */
const loading = ref(true)
/** Currently selected year for budget viewing */
const year = ref(new Date().getFullYear())
/** Currently selected month (1-12) for budget viewing */
const month = ref(new Date().getMonth() + 1)

/** Controls visibility of the "create new budget" dialog */
const showCreate = ref(false)
/** Form data for the new budget: target category ID and spending limit amount */
const newBudget = ref({
  category: null as number | null,
  amount_limit: 0,
})

/**
 * Fetches budgets for the current year/month and the full category list in parallel.
 * Budgets are scoped to the selected month and year via query parameters.
 */
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

/**
 * Creates a new budget for the current month/year.
 * Validates that a category is selected and the amount limit is positive,
 * then calls the API and reloads data. Closes the dialog and resets the form on success.
 */
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

/**
 * Deletes a budget by ID and reloads all data to reflect the removal.
 */
async function deleteBudget(id: number) {
  await budgetsApi.delete(id)
  await loadData()
}

/** Italian month names for the month navigation header */
const months = [
  'Gennaio', 'Febbraio', 'Marzo', 'Aprile', 'Maggio', 'Giugno',
  'Luglio', 'Agosto', 'Settembre', 'Ottobre', 'Novembre', 'Dicembre',
]

/** Navigates to the previous month, wrapping from January to December of the previous year. */
function prevMonth() {
  if (month.value === 1) {
    month.value = 12
    year.value--
  } else {
    month.value--
  }
}

/** Navigates to the next month, wrapping from December to January of the next year. */
function nextMonth() {
  if (month.value === 12) {
    month.value = 1
    year.value++
  } else {
    month.value++
  }
}

/**
 * Returns the progress bar variant based on the percentage of budget used.
 * - 'destructive' at 100% or more (budget exceeded)
 * - 'warning' at 80% or more (approaching limit)
 * - 'default' below 80%
 */
function getProgressVariant(pct: number): 'default' | 'warning' | 'destructive' {
  if (pct >= 100) return 'destructive'
  if (pct >= 80) return 'warning'
  return 'default'
}

// Fetch data on initial mount
onMounted(loadData)
// Re-fetch whenever the selected year or month changes
watch([year, month], loadData)
</script>

<template>
  <div>
    <div class="mb-6 flex flex-wrap items-center justify-between gap-4">
      <h1 class="text-2xl font-bold tracking-tight">Budget</h1>
      <Dialog v-model:open="showCreate">
        <DialogTrigger as-child>
          <Button>
            <Plus class="mr-1 size-4" />
            Nuovo budget
          </Button>
        </DialogTrigger>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Nuovo budget</DialogTitle>
            <DialogDescription>
              Imposta un limite di spesa per una categoria nel mese corrente.
            </DialogDescription>
          </DialogHeader>
          <div class="space-y-4 py-4">
            <div class="space-y-2">
              <Label>Categoria</Label>
              <Select v-model="newBudget.category">
                <SelectTrigger>
                  <SelectValue placeholder="Seleziona categoria" />
                </SelectTrigger>
                <SelectContent>
                  <SelectItem
                    v-for="cat in categories"
                    :key="cat.id"
                    :value="cat.id"
                  >
                    {{ cat.name }}
                  </SelectItem>
                </SelectContent>
              </Select>
            </div>
            <div class="space-y-2">
              <Label for="budget-limit">Limite (€)</Label>
              <Input
                id="budget-limit"
                v-model.number="newBudget.amount_limit"
                type="number"
                min="0"
                step="1"
              />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" @click="showCreate = false">Annulla</Button>
            <Button @click="createBudget">Crea</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>

    <Card class="mb-6">
      <CardContent class="flex items-center justify-between py-4">
        <Button variant="outline" size="icon" @click="prevMonth">
          <ChevronLeft class="size-4" />
        </Button>
        <span class="text-lg font-semibold">
          {{ months[month - 1] }} {{ year }}
        </span>
        <Button variant="outline" size="icon" @click="nextMonth">
          <ChevronRight class="size-4" />
        </Button>
      </CardContent>
    </Card>

    <template v-if="loading">
      <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <Skeleton v-for="i in 3" :key="i" class="h-36" />
      </div>
    </template>
    <template v-else-if="!budgets.length">
      <Card>
        <CardContent class="py-12 text-center">
          <p class="text-muted-foreground">Nessun budget definito per questo mese</p>
        </CardContent>
      </Card>
    </template>
    <template v-else>
      <div class="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
        <Card v-for="b in budgets" :key="b.id">
          <CardHeader class="pb-2">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-2">
                <span class="size-3 rounded-full" :style="{ backgroundColor: b.category_color }" />
                <CardTitle class="text-base">{{ b.category_name }}</CardTitle>
              </div>
              <AlertDialog>
                <AlertDialogTrigger as-child>
                  <Button size="icon" variant="ghost" class="text-destructive hover:text-destructive">
                    <Trash2 class="size-4" />
                  </Button>
                </AlertDialogTrigger>
                <AlertDialogContent>
                  <AlertDialogHeader>
                    <AlertDialogTitle>Eliminare il budget?</AlertDialogTitle>
                    <AlertDialogDescription>
                      Il budget per {{ b.category_name }} verrà eliminato definitivamente.
                    </AlertDialogDescription>
                  </AlertDialogHeader>
                  <AlertDialogFooter>
                    <AlertDialogCancel>Annulla</AlertDialogCancel>
                    <AlertDialogAction
                      class="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                      @click="deleteBudget(b.id)"
                    >
                      Elimina
                    </AlertDialogAction>
                  </AlertDialogFooter>
                </AlertDialogContent>
              </AlertDialog>
            </div>
          </CardHeader>
          <CardContent>
            <div class="mb-2 flex justify-between text-sm">
              <span class="font-mono tabular-nums">{{ formatCurrency(b.current_spent) }}</span>
              <span class="text-muted-foreground font-mono tabular-nums">{{ formatCurrency(b.amount_limit) }}</span>
            </div>
            <Progress :model-value="Math.min(b.percentage, 100)" class="h-2" />
            <div class="mt-2 flex items-center justify-between text-xs">
              <span class="text-muted-foreground">{{ b.percentage }}% utilizzato</span>
              <Badge v-if="b.percentage >= 100" variant="destructive">Budget superato!</Badge>
              <Badge v-else-if="b.percentage >= 80" variant="secondary">Attenzione</Badge>
              <span v-else class="font-medium text-income">
                {{ formatCurrency(b.amount_limit - b.current_spent) }} rimanenti
              </span>
            </div>
          </CardContent>
        </Card>
      </div>
    </template>
  </div>
</template>