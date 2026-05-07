<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { categoriesApi } from '@/api'
import type { Category, CategoryRule } from '@/types'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Label } from '@/components/ui/label'
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
import { Plus, Trash2, ArrowRight, Tag } from 'lucide-vue-next'

const categories = ref<Category[]>([])
const rules = ref<CategoryRule[]>([])
const loading = ref(true)

const showCreateCategory = ref(false)
const newCatName = ref('')
const newCatColor = ref('#3B82F6')

const showCreateRule = ref(false)
const newRuleKeyword = ref('')
const newRuleCategory = ref<number | null>(null)

async function loadData() {
  loading.value = true
  try {
    const [catRes, ruleRes] = await Promise.all([categoriesApi.list(), categoriesApi.rules()])
    categories.value = catRes.data
    rules.value = ruleRes.data
  } finally {
    loading.value = false
  }
}

async function createCategory() {
  if (!newCatName.value.trim()) return
  await categoriesApi.create({ name: newCatName.value.trim(), color: newCatColor.value })
  newCatName.value = ''
  showCreateCategory.value = false
  await loadData()
}

async function createRule() {
  if (!newRuleKeyword.value.trim() || !newRuleCategory.value) return
  await categoriesApi.createRule({
    keyword: newRuleKeyword.value.trim(),
    category: newRuleCategory.value,
    priority: 0,
  })
  newRuleKeyword.value = ''
  newRuleCategory.value = null
  showCreateRule.value = false
  await loadData()
}

async function deleteCategory(id: number) {
  await categoriesApi.delete(id)
  await loadData()
}

async function deleteRule(id: number) {
  await categoriesApi.deleteRule(id)
  await loadData()
}

onMounted(loadData)
</script>

<template>
  <div>
    <h1 class="mb-6 text-2xl font-bold tracking-tight">Categorie</h1>

    <div class="mb-8">
      <h2 class="mb-4 text-lg font-semibold">Categorie di sistema</h2>
      <div class="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4">
        <Card v-for="cat in categories.filter((c) => c.is_system)" :key="cat.id">
          <CardContent class="flex items-center gap-3 p-4">
            <span
              class="flex size-8 items-center justify-center rounded-lg text-sm"
              :style="{ backgroundColor: `${cat.color}20`, color: cat.color }"
            >
              ●
            </span>
            <span class="text-sm font-medium">{{ cat.name }}</span>
          </CardContent>
        </Card>
      </div>
    </div>

    <div class="mb-8">
      <div class="mb-4 flex items-center justify-between">
        <h2 class="text-lg font-semibold">Categorie personalizzate</h2>
        <Dialog v-model:open="showCreateCategory">
          <DialogTrigger as-child>
            <Button size="sm">
              <Plus class="mr-1 size-4" />
              Nuova
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Nuova categoria</DialogTitle>
              <DialogDescription>Crea una categoria personalizzata per le tue transazioni.</DialogDescription>
            </DialogHeader>
            <div class="space-y-4 py-4">
              <div class="space-y-2">
                <Label for="cat-name">Nome</Label>
                <Input id="cat-name" v-model="newCatName" placeholder="Nome categoria" />
              </div>
              <div class="space-y-2">
                <Label for="cat-color">Colore</Label>
                <div class="flex items-center gap-3">
                  <input id="cat-color" v-model="newCatColor" type="color" class="h-10 w-16 rounded border border-input" />
                  <span class="text-sm text-muted-foreground">{{ newCatColor }}</span>
                </div>
              </div>
            </div>
            <DialogFooter>
              <Button variant="outline" @click="showCreateCategory = false">Annulla</Button>
              <Button @click="createCategory">Crea</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      <template v-if="loading">
        <div class="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4">
          <Skeleton v-for="i in 4" :key="i" class="h-16" />
        </div>
      </template>
      <template v-else>
        <div v-if="!categories.filter((c) => !c.is_system).length">
          <Card>
            <CardContent class="py-8 text-center">
              <p class="text-muted-foreground">Nessuna categoria personalizzata</p>
            </CardContent>
          </Card>
        </div>
        <div v-else class="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4">
          <Card v-for="cat in categories.filter((c) => !c.is_system)" :key="cat.id">
            <CardContent class="flex items-center justify-between p-4">
              <div class="flex items-center gap-3">
                <span
                  class="flex size-8 items-center justify-center rounded-lg text-sm"
                  :style="{ backgroundColor: `${cat.color}20`, color: cat.color }"
                >
                  ●
                </span>
                <span class="text-sm font-medium">{{ cat.name }}</span>
              </div>
              <AlertDialog>
                <AlertDialogTrigger as-child>
                  <Button size="icon" variant="ghost" class="text-destructive hover:text-destructive">
                    <Trash2 class="size-4" />
                  </Button>
                </AlertDialogTrigger>
                <AlertDialogContent>
                  <AlertDialogHeader>
                    <AlertDialogTitle>Eliminare la categoria?</AlertDialogTitle>
                    <AlertDialogDescription>
                      Le transazioni associate andranno in "Altro". Questa azione non può essere annullata.
                    </AlertDialogDescription>
                  </AlertDialogHeader>
                  <AlertDialogFooter>
                    <AlertDialogCancel>Annulla</AlertDialogCancel>
                    <AlertDialogAction
                      class="bg-destructive text-destructive-foreground hover:bg-destructive/90"
                      @click="deleteCategory(cat.id)"
                    >
                      Elimina
                    </AlertDialogAction>
                  </AlertDialogFooter>
                </AlertDialogContent>
              </AlertDialog>
            </CardContent>
          </Card>
        </div>
      </template>
    </div>

    <div>
      <div class="mb-4 flex items-center justify-between">
        <h2 class="text-lg font-semibold">Regole di auto-categorizzazione</h2>
        <Dialog v-model:open="showCreateRule">
          <DialogTrigger as-child>
            <Button size="sm">
              <Plus class="mr-1 size-4" />
              Nuova regola
            </Button>
          </DialogTrigger>
          <DialogContent>
            <DialogHeader>
              <DialogTitle>Nuova regola</DialogTitle>
              <DialogDescription>
                Le transazioni con la keyword nel campo descrizione verranno categorizzate automaticamente.
              </DialogDescription>
            </DialogHeader>
            <div class="space-y-4 py-4">
              <div class="space-y-2">
                <Label for="rule-keyword">Keyword</Label>
                <Input
                  id="rule-keyword"
                  v-model="newRuleKeyword"
                  placeholder="Es. Netflix, Amazon, Trenord..."
                />
              </div>
              <div class="space-y-2">
                <Label>Categoria</Label>
                <Select v-model="newRuleCategory">
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
            </div>
            <DialogFooter>
              <Button variant="outline" @click="showCreateRule = false">Annulla</Button>
              <Button @click="createRule">Crea</Button>
            </DialogFooter>
          </DialogContent>
        </Dialog>
      </div>

      <template v-if="loading">
        <Skeleton class="h-48" />
      </template>
      <template v-else>
        <Card v-if="!rules.length">
          <CardContent class="py-8 text-center">
            <Tag class="mx-auto mb-2 size-8 text-muted-foreground" />
            <p class="text-muted-foreground">Nessuna regola definita. Crea una regola per categorizzare automaticamente le transazioni.</p>
          </CardContent>
        </Card>
        <Card v-else>
          <CardContent class="p-0">
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Keyword</TableHead>
                  <TableHead>Categoria</TableHead>
                  <TableHead class="w-16" />
                </TableRow>
              </TableHeader>
              <TableBody>
                <TableRow v-for="rule in rules" :key="rule.id">
                  <TableCell class="font-mono">"{{ rule.keyword }}"</TableCell>
                  <TableCell>
                    <Badge
                      :style="{
                        backgroundColor: `${rule.category_color}20`,
                        color: rule.category_color,
                      }"
                      variant="secondary"
                    >
                      {{ rule.category_name }}
                    </Badge>
                  </TableCell>
                  <TableCell>
                    <Button size="icon" variant="ghost" class="text-destructive hover:text-destructive" @click="deleteRule(rule.id)">
                      <Trash2 class="size-4" />
                    </Button>
                  </TableCell>
                </TableRow>
              </TableBody>
            </Table>
          </CardContent>
        </Card>
      </template>
    </div>
  </div>
</template>