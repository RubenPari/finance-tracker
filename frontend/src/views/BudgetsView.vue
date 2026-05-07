<script setup lang="ts">
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
  'Gennaio', 'Febbraio', 'Marzo', 'Aprile', 'Maggio', 'Giugno',
  'Luglio', 'Agosto', 'Settembre', 'Ottobre', 'Novembre', 'Dicembre',
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

function getProgressVariant(pct: number): 'default' | 'warning' | 'destructive' {
  if (pct >= 100) return 'destructive'
  if (pct >= 80) return 'warning'
  return 'default'
}

onMounted(loadData)
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