<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { transactionsApi } from '@/api'
import type { ImportBatch } from '@/types'
import { formatDateTime } from '@/utils/formatters'

const fileInput = ref<HTMLInputElement | null>(null)
const dragging = ref(false)
const uploading = ref(false)
const result = ref<ImportBatch | null>(null)
const error = ref('')
const history = ref<ImportBatch[]>([])

let pollTimer: ReturnType<typeof setInterval> | null = null

function onDragOver(e: DragEvent) {
  e.preventDefault()
  dragging.value = true
}

function onDragLeave() {
  dragging.value = false
}

async function onDrop(e: DragEvent) {
  e.preventDefault()
  dragging.value = false
  const file = e.dataTransfer?.files?.[0]
  if (file) await upload(file)
}

async function onFileSelect(e: Event) {
  const input = e.target as HTMLInputElement
  const file = input.files?.[0]
  if (file) await upload(file)
  input.value = ''
}

async function upload(file: File) {
  error.value = ''
  result.value = null

  if (!file.name.toLowerCase().endsWith('.xlsx')) {
    error.value = 'Formato non supportato. Carica un file .xlsx.'
    return
  }

  uploading.value = true
  try {
    const { data } = await transactionsApi.import(file)
    result.value = data

    if (data.status === 'PROCESSING') {
      startPolling(data.id)
    }
  } catch (e: unknown) {
    const resp = (e as { response?: { data?: { error?: string } } }).response
    error.value = resp?.data?.error || 'Errore durante l\'upload del file.'
  } finally {
    uploading.value = false
  }
}

async function startPolling(batchId: number) {
  pollTimer = setInterval(async () => {
    try {
      const { data } = await transactionsApi.importDetail(batchId)
      result.value = data
      if (data.status === 'COMPLETED' || data.status === 'FAILED') {
        stopPolling()
        await loadHistory()
      }
    } catch {
      stopPolling()
    }
  }, 1500)
}

function stopPolling() {
  if (pollTimer) {
    clearInterval(pollTimer)
    pollTimer = null
  }
}

async function loadHistory() {
  try {
    const { data } = await transactionsApi.importHistory()
    history.value = data
  } catch {}
}

onMounted(loadHistory)
onUnmounted(stopPolling)
</script>

<template>
  <div>
    <h1 class="mb-6 text-2xl font-bold text-gray-900">Importa CSV</h1>

    <form v-if="!uploading && !result" class="card">
      <div
        class="flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed p-12 transition-colors"
        :class="dragging ? 'border-blue-500 bg-blue-50' : 'border-gray-300'"
        @dragover="onDragOver"
        @dragleave="onDragLeave"
        @drop="onDrop"
        @click="fileInput?.click()"
      >
        <span class="mb-3 text-4xl">📄</span>
        <p class="text-lg font-medium text-gray-700">
          Trascina il file XLSX di Revolut qui
        </p>
        <p class="mt-1 text-sm text-gray-400">oppure clicca per selezionare</p>
        <input
          ref="fileInput"
          type="file"
          accept=".xlsx"
          class="hidden"
          @change="onFileSelect"
        />
      </div>
      <div v-if="error" class="mt-4 rounded-lg bg-red-50 px-4 py-3 text-sm text-red-700">
        {{ error }}
      </div>
    </form>

    <div v-if="uploading && result" class="card text-center">
      <div class="mx-auto mb-4 h-10 w-10 animate-spin rounded-full border-4 border-blue-600 border-t-transparent" />
      <p class="font-medium text-gray-700">Elaborazione in corso...</p>
      <p class="mt-1 text-sm text-gray-400">Importazione di {{ result.filename }}</p>
    </div>

    <div v-if="result && result.status === 'COMPLETED'" class="card">
      <div class="mb-4 text-center">
        <span class="text-4xl">✅</span>
        <h2 class="mt-2 text-xl font-semibold text-gray-900">Import completato!</h2>
      </div>

      <div class="grid grid-cols-2 gap-4 sm:grid-cols-4">
        <div class="rounded-lg bg-green-50 p-4 text-center">
          <p class="text-2xl font-bold text-green-700">{{ result.imported_count }}</p>
          <p class="text-xs text-green-600">Importate</p>
        </div>
        <div class="rounded-lg bg-yellow-50 p-4 text-center">
          <p class="text-2xl font-bold text-yellow-700">{{ result.skipped_count }}</p>
          <p class="text-xs text-yellow-600">Duplicate</p>
        </div>
        <div class="rounded-lg bg-gray-100 p-4 text-center">
          <p class="text-2xl font-bold text-gray-700">
            {{ result.total_rows - result.imported_count - result.skipped_count - result.error_count }}
          </p>
          <p class="text-xs text-gray-500">Scartate</p>
        </div>
        <div class="rounded-lg bg-red-50 p-4 text-center">
          <p class="text-2xl font-bold text-red-700">{{ result.error_count }}</p>
          <p class="text-xs text-red-600">Errori</p>
        </div>
      </div>

      <div class="mt-6 flex justify-center gap-3">
        <RouterLink to="/transactions" class="btn-primary">Vedi transazioni</RouterLink>
        <button class="btn-secondary" @click="result = null">Importa un altro file</button>
      </div>
    </div>

    <div v-if="result && result.status === 'FAILED'" class="card text-center">
      <span class="text-4xl">❌</span>
      <h2 class="mt-2 text-xl font-semibold text-red-600">Import fallito</h2>
      <p class="mt-1 text-sm text-gray-500">Il file potrebbe non essere nel formato atteso.</p>
      <button class="btn-secondary mt-4" @click="result = null">Riprova</button>
    </div>

    <div v-if="history.length" class="mt-8">
      <h2 class="mb-4 text-lg font-semibold text-gray-900">Storico import</h2>
      <div class="card">
        <div class="space-y-3">
          <div
            v-for="batch in history"
            :key="batch.id"
            class="flex items-center justify-between rounded-lg bg-gray-50 px-4 py-3"
          >
            <div>
              <p class="text-sm font-medium text-gray-900">{{ batch.filename }}</p>
              <p class="text-xs text-gray-400">{{ formatDateTime(batch.imported_at) }}</p>
            </div>
            <div class="flex gap-4 text-xs">
              <span class="text-green-600">{{ batch.imported_count }} importate</span>
              <span class="text-yellow-600">{{ batch.skipped_count }} duplicate</span>
              <span v-if="batch.error_count" class="text-red-600">{{ batch.error_count }} errori</span>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>
