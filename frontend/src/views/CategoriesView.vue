<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { categoriesApi } from '@/api'
import type { Category, CategoryRule } from '@/types'

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
  if (!confirm('Eliminare questa categoria? Le transazioni associate andranno in "Altro".')) return
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
    <h1 class="mb-6 text-2xl font-bold text-gray-900">Categorie</h1>

    <div class="mb-8">
      <div class="mb-4 flex items-center justify-between">
        <h2 class="text-lg font-semibold text-gray-900">Categorie di sistema</h2>
      </div>
      <div class="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4">
        <div
          v-for="cat in categories.filter((c) => c.is_system)"
          :key="cat.id"
          class="card flex items-center gap-3 p-4"
        >
          <span
            class="flex h-8 w-8 items-center justify-center rounded-lg text-sm"
            :style="{ backgroundColor: `${cat.color}20`, color: cat.color }"
          >
            ●
          </span>
          <span class="text-sm font-medium text-gray-900">{{ cat.name }}</span>
        </div>
      </div>
    </div>

    <div class="mb-8">
      <div class="mb-4 flex items-center justify-between">
        <h2 class="text-lg font-semibold text-gray-900">Categorie personalizzate</h2>
        <button class="btn-primary text-sm" @click="showCreateCategory = !showCreateCategory">
          + Nuova
        </button>
      </div>

      <div v-if="showCreateCategory" class="card mb-4">
        <div class="flex items-end gap-3">
          <div class="flex-1">
            <label class="mb-1 block text-xs font-medium text-gray-600">Nome</label>
            <input v-model="newCatName" type="text" class="input-field" placeholder="Nome categoria" />
          </div>
          <div>
            <label class="mb-1 block text-xs font-medium text-gray-600">Colore</label>
            <input v-model="newCatColor" type="color" class="h-10 w-16 rounded border border-gray-300" />
          </div>
          <button class="btn-primary" @click="createCategory">Crea</button>
          <button class="btn-secondary" @click="showCreateCategory = false">Annulla</button>
        </div>
      </div>

      <div class="grid grid-cols-2 gap-3 sm:grid-cols-3 md:grid-cols-4">
        <div
          v-for="cat in categories.filter((c) => !c.is_system)"
          :key="cat.id"
          class="card flex items-center justify-between p-4"
        >
          <div class="flex items-center gap-3">
            <span
              class="flex h-8 w-8 items-center justify-center rounded-lg text-sm"
              :style="{ backgroundColor: `${cat.color}20`, color: cat.color }"
            >
              ●
            </span>
            <span class="text-sm font-medium text-gray-900">{{ cat.name }}</span>
          </div>
          <button
            class="text-xs text-red-500 hover:text-red-700"
            @click="deleteCategory(cat.id)"
          >
            Elimina
          </button>
        </div>
        <div v-if="!categories.filter((c) => !c.is_system).length" class="col-span-full py-4 text-center text-sm text-gray-400">
          Nessuna categoria personalizzata
        </div>
      </div>
    </div>

    <div>
      <div class="mb-4 flex items-center justify-between">
        <h2 class="text-lg font-semibold text-gray-900">Regole di auto-categorizzazione</h2>
        <button class="btn-primary text-sm" @click="showCreateRule = !showCreateRule">
          + Nuova regola
        </button>
      </div>

      <div v-if="showCreateRule" class="card mb-4">
        <div class="flex items-end gap-3">
          <div class="flex-1">
            <label class="mb-1 block text-xs font-medium text-gray-600">Keyword</label>
            <input
              v-model="newRuleKeyword"
              type="text"
              class="input-field"
              placeholder="Es. Netflix, Amazon, Trenord..."
            />
          </div>
          <div>
            <label class="mb-1 block text-xs font-medium text-gray-600">Categoria</label>
            <select v-model="newRuleCategory" class="input-field">
              <option :value="null">Seleziona...</option>
              <option v-for="cat in categories" :key="cat.id" :value="cat.id">
                {{ cat.name }}
              </option>
            </select>
          </div>
          <button class="btn-primary" @click="createRule">Crea</button>
          <button class="btn-secondary" @click="showCreateRule = false">Annulla</button>
        </div>
      </div>

      <div v-if="loading" class="flex justify-center py-8">
        <div class="h-6 w-6 animate-spin rounded-full border-3 border-blue-600 border-t-transparent" />
      </div>

      <div v-else-if="!rules.length" class="card py-8 text-center text-sm text-gray-400">
        Nessuna regola definita. Crea una regola per categorizzare automaticamente le transazioni.
      </div>

      <div v-else class="card">
        <div class="space-y-2">
          <div
            v-for="rule in rules"
            :key="rule.id"
            class="flex items-center justify-between rounded-lg bg-gray-50 px-4 py-2"
          >
            <div class="flex items-center gap-3">
              <span class="text-sm font-mono text-gray-700">"{{ rule.keyword }}"</span>
              <span class="text-xs text-gray-400">→</span>
              <span
                class="rounded-full px-2 py-0.5 text-xs font-medium"
                :style="{ backgroundColor: `${rule.category_color}20`, color: rule.category_color }"
              >
                {{ rule.category_name }}
              </span>
            </div>
            <button
              class="text-xs text-red-500 hover:text-red-700"
              @click="deleteRule(rule.id)"
            >
              Elimina
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
