<script setup lang="ts">
import { ref, onMounted, onUnmounted } from 'vue'
import { transactionsApi } from '@/api'
import type { ImportBatch, Transaction } from '@/types'
import { formatDateTime, formatDate, formatCurrency } from '@/utils/formatters'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
import { Input } from '@/components/ui/input'
import { Skeleton } from '@/components/ui/skeleton'
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from '@/components/ui/table'
import {
  Collapsible,
  CollapsibleContent,
  CollapsibleTrigger,
} from '@/components/ui/collapsible'
import { Upload, CheckCircle2, XCircle, Loader2, ChevronDown, FileSpreadsheet } from 'lucide-vue-next'

const fileInput = ref<HTMLInputElement | null>(null)
const dragging = ref(false)
const uploading = ref(false)
const result = ref<ImportBatch | null>(null)
const error = ref('')
const history = ref<ImportBatch[]>([])
const expandedBatch = ref<number | null>(null)
const isExpanded = ref(false)
const batchTransactions = ref<Transaction[]>([])
const batchTransactionLoading = ref(false)
const batchTransactionPage = ref(1)
const batchTransactionTotal = ref(0)
const batchTransactionHasNext = ref(false)
const batchTransactionHasPrev = ref(false)

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
    error.value = resp?.data?.error || "Errore durante l'upload del file."
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

async function toggleBatch(batch: ImportBatch) {
  if (expandedBatch.value === batch.id) {
    expandedBatch.value = null
    isExpanded.value = false
    batchTransactions.value = []
    return
  }

  expandedBatch.value = batch.id
  isExpanded.value = true
  batchTransactionPage.value = 1
  await loadBatchTransactions(batch.id, 1)
}

async function loadBatchTransactions(batchId: number, page: number) {
  batchTransactionLoading.value = true
  try {
    const { data } = await transactionsApi.batchTransactions(batchId, { page })
    batchTransactions.value = data.results
    batchTransactionTotal.value = data.count
    batchTransactionHasNext.value = !!data.next
    batchTransactionHasPrev.value = !!data.previous
    batchTransactionPage.value = page
  } catch {
    batchTransactions.value = []
  } finally {
    batchTransactionLoading.value = false
  }
}

function getStatusBadgeVariant(status: string): 'secondary' | 'default' | 'destructive' {
  const map: Record<string, 'secondary' | 'default' | 'destructive'> = {
    PENDING: 'secondary',
    PROCESSING: 'default',
    COMPLETED: 'default',
    FAILED: 'destructive',
  }
  return map[status] || 'secondary'
}

function getStatusLabel(status: string): string {
  const map: Record<string, string> = {
    PENDING: 'In attesa',
    PROCESSING: 'In elaborazione',
    COMPLETED: 'Completato',
    FAILED: 'Fallito',
  }
  return map[status] || status
}

onMounted(loadHistory)
onUnmounted(stopPolling)
</script>

<template>
  <div>
    <h1 class="mb-6 text-2xl font-bold tracking-tight">Importa XLSX</h1>

    <template v-if="!uploading && !result">
      <Card>
        <CardContent class="pt-6">
          <div
            class="flex cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed border-muted-foreground/25 p-12 transition-colors hover:border-primary hover:bg-muted/50"
            :class="{ 'border-primary bg-muted/50': dragging }"
            @dragover="onDragOver"
            @dragleave="onDragLeave"
            @drop="onDrop"
            @click="fileInput?.click()"
          >
            <Upload class="mb-3 size-10 text-muted-foreground" />
            <p class="text-lg font-medium">Trascina il file XLSX di Revolut qui</p>
            <p class="mt-1 text-sm text-muted-foreground">oppure clicca per selezionare</p>
            <input ref="fileInput" type="file" accept=".xlsx" class="hidden" @change="onFileSelect" />
          </div>
          <div
            v-if="error"
            class="mt-4 rounded-lg border border-destructive/50 bg-destructive/10 px-4 py-3 text-sm text-destructive"
          >
            {{ error }}
          </div>
        </CardContent>
      </Card>
    </template>

    <template v-if="uploading && result">
      <Card>
        <CardContent class="flex flex-col items-center py-12">
          <Loader2 class="mb-4 size-10 animate-spin text-primary" />
          <p class="font-medium">Elaborazione in corso...</p>
          <p class="mt-1 text-sm text-muted-foreground">Importazione di {{ result.filename }}</p>
        </CardContent>
      </Card>
    </template>

    <template v-if="result && result.status === 'COMPLETED'">
      <Card>
        <CardContent class="pt-6">
          <div class="mb-6 text-center">
            <CheckCircle2 class="mx-auto size-10 text-income" />
            <h2 class="mt-2 text-xl font-semibold">Import completato!</h2>
          </div>

          <div class="grid grid-cols-2 gap-4 sm:grid-cols-4">
            <Card class="border-l-4 border-l-income">
              <CardContent class="pt-4 pb-4 text-center">
                <p class="text-2xl font-bold font-mono tabular-nums text-income">{{ result.imported_count }}</p>
                <p class="text-xs text-muted-foreground">Importate</p>
              </CardContent>
            </Card>
            <Card class="border-l-4 border-l-warning">
              <CardContent class="pt-4 pb-4 text-center">
                <p class="text-2xl font-bold font-mono tabular-nums text-warning">{{ result.skipped_count }}</p>
                <p class="text-xs text-muted-foreground">Duplicate</p>
              </CardContent>
            </Card>
            <Card>
              <CardContent class="pt-4 pb-4 text-center">
                <p class="text-2xl font-bold font-mono tabular-nums text-muted-foreground">
                  {{ result.total_rows - result.imported_count - result.skipped_count - result.error_count }}
                </p>
                <p class="text-xs text-muted-foreground">Scartate</p>
              </CardContent>
            </Card>
            <Card v-if="result.error_count" class="border-l-4 border-l-destructive">
              <CardContent class="pt-4 pb-4 text-center">
                <p class="text-2xl font-bold font-mono tabular-nums text-destructive">{{ result.error_count }}</p>
                <p class="text-xs text-muted-foreground">Errori</p>
              </CardContent>
            </Card>
          </div>

          <div class="mt-6 flex justify-center gap-3">
            <RouterLink to="/transactions">
              <Button>Vedi transazioni</Button>
            </RouterLink>
            <Button variant="outline" @click="result = null">Importa un altro file</Button>
          </div>
        </CardContent>
      </Card>
    </template>

    <template v-if="result && result.status === 'FAILED'">
      <Card>
        <CardContent class="flex flex-col items-center py-12">
          <XCircle class="mb-2 size-10 text-destructive" />
          <h2 class="text-xl font-semibold text-destructive">Import fallito</h2>
          <p class="mt-1 text-sm text-muted-foreground">Il file potrebbe non essere nel formato atteso.</p>
          <Button variant="outline" class="mt-4" @click="result = null">Riprova</Button>
        </CardContent>
      </Card>
    </template>

    <div v-if="history.length" class="mt-8">
      <h2 class="mb-4 text-lg font-semibold">Storico import</h2>
      <div class="space-y-3">
        <Card v-for="batch in history" :key="batch.id">
          <Collapsible v-model:open="isExpanded" @update:open="toggleBatch(batch)">
            <CollapsibleTrigger as-child>
              <button
                class="flex w-full items-center justify-between px-4 py-3 text-left transition-colors hover:bg-muted/50"
              >
                <div class="flex items-center gap-3">
                  <ChevronDown class="size-4 text-muted-foreground transition-transform" />
                  <div>
                    <p class="text-sm font-medium">{{ batch.filename }}</p>
                    <p class="text-xs text-muted-foreground">{{ formatDateTime(batch.imported_at) }}</p>
                  </div>
                </div>
                <div class="flex items-center gap-4">
                  <Badge :variant="getStatusBadgeVariant(batch.status)">
                    {{ getStatusLabel(batch.status) }}
                  </Badge>
                  <div class="flex gap-3 text-xs">
                    <span class="text-income">{{ batch.imported_count }} importate</span>
                    <span class="text-warning">{{ batch.skipped_count }} duplicate</span>
                    <span v-if="batch.error_count" class="text-destructive">{{ batch.error_count }} errori</span>
                  </div>
                </div>
              </button>
            </CollapsibleTrigger>
            <CollapsibleContent>
              <div class="border-t px-4">
                <template v-if="batchTransactionLoading">
                  <div class="flex justify-center py-8">
                    <Loader2 class="size-6 animate-spin text-primary" />
                  </div>
                </template>
                <template v-else-if="batchTransactions.length === 0">
                  <p class="py-6 text-center text-sm text-muted-foreground">
                    Nessuna transazione trovata per questo batch.
                  </p>
                </template>
                <template v-else>
                  <Table>
                    <TableHeader>
                      <TableRow>
                        <TableHead>Data</TableHead>
                        <TableHead>Descrizione</TableHead>
                        <TableHead>Categoria</TableHead>
                        <TableHead>Tipo</TableHead>
                        <TableHead class="text-right">Importo</TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      <TableRow v-for="tx in batchTransactions" :key="tx.id">
                        <TableCell class="whitespace-nowrap text-muted-foreground">
                          {{ formatDate(tx.completed_at) }}
                        </TableCell>
                        <TableCell class="font-medium">{{ tx.description }}</TableCell>
                        <TableCell>
                          <Badge
                            v-if="tx.category_name"
                            :style="{
                              backgroundColor: `${tx.category_color}20`,
                              color: tx.category_color,
                            }"
                            variant="secondary"
                          >
                            {{ tx.category_name }}
                          </Badge>
                          <span v-else class="text-muted-foreground">—</span>
                        </TableCell>
                        <TableCell class="whitespace-nowrap text-muted-foreground">
                          {{ tx.transaction_type }}
                        </TableCell>
                        <TableCell
                          class="whitespace-nowrap text-right font-mono tabular-nums font-medium"
                          :class="tx.amount < 0 ? 'text-expense' : 'text-income'"
                        >
                          {{ formatCurrency(tx.amount) }}
                        </TableCell>
                      </TableRow>
                    </TableBody>
                  </Table>

                  <div
                    v-if="batchTransactionHasPrev || batchTransactionHasNext"
                    class="flex items-center justify-between border-t py-3"
                  >
                    <p class="text-xs text-muted-foreground">
                      {{ batchTransactionTotal }} transazioni
                    </p>
                    <div class="flex gap-2">
                      <Button
                        v-if="batchTransactionHasPrev"
                        variant="outline"
                        size="sm"
                        @click.stop="loadBatchTransactions(batch.id, batchTransactionPage - 1)"
                      >
                        Precedente
                      </Button>
                      <Button
                        v-if="batchTransactionHasNext"
                        variant="outline"
                        size="sm"
                        @click.stop="loadBatchTransactions(batch.id, batchTransactionPage + 1)"
                      >
                        Successiva
                      </Button>
                    </div>
                  </div>
                </template>
              </div>
            </CollapsibleContent>
          </Collapsible>
        </Card>
      </div>
    </div>
  </div>
</template>