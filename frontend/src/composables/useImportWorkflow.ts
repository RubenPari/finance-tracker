import { onMounted, onUnmounted, ref } from 'vue'
import { transactionsApi } from '@/api'
import type { ImportBatch, Transaction } from '@/types'
import { getApiErrorMessage } from '@/utils/http'

export function useImportWorkflow() {
  const fileInput = ref<HTMLInputElement | null>(null)
  const dragging = ref(false)
  const uploading = ref(false)
  const committing = ref(false)
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
      error.value = getApiErrorMessage(e, "Errore durante l'upload del file.")
    } finally {
      uploading.value = false
    }
  }

  async function startPolling(batchId: number) {
    pollTimer = setInterval(async () => {
      try {
        const { data } = await transactionsApi.importDetail(batchId)
        result.value = data
        if (data.status === 'STAGED' || data.status === 'COMPLETED' || data.status === 'FAILED') {
          stopPolling()
          await loadHistory()
        }
      } catch (e) {
        console.error('Polling import batch fallito:', e)
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
    } catch (e) {
      console.error('Caricamento storico import fallito:', e)
    }
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
    } catch (e) {
      console.error('Caricamento transazioni batch fallito:', e)
      batchTransactions.value = []
    } finally {
      batchTransactionLoading.value = false
    }
  }

  async function commitImport(batchId: number) {
    error.value = ''
    committing.value = true
    try {
      await transactionsApi.commitImport(batchId)
      const { data } = await transactionsApi.importDetail(batchId)
      result.value = data
      await loadHistory()
    } catch (e: unknown) {
      error.value = getApiErrorMessage(e, "Errore durante la conferma dell'import.")
    } finally {
      committing.value = false
    }
  }

  function getStatusBadgeVariant(status: string): 'secondary' | 'default' | 'destructive' {
    const map: Record<string, 'secondary' | 'default' | 'destructive'> = {
      PENDING: 'secondary',
      PROCESSING: 'default',
      STAGED: 'secondary',
      COMPLETED: 'default',
      FAILED: 'destructive',
    }
    return map[status] || 'secondary'
  }

  function getStatusLabel(status: string): string {
    const map: Record<string, string> = {
      PENDING: 'In attesa',
      PROCESSING: 'In elaborazione',
      STAGED: 'In revisione',
      COMPLETED: 'Completato',
      FAILED: 'Fallito',
    }
    return map[status] || status
  }

  onMounted(loadHistory)
  onUnmounted(stopPolling)

  return {
    fileInput,
    dragging,
    uploading,
    committing,
    result,
    error,
    history,
    expandedBatch,
    isExpanded,
    batchTransactions,
    batchTransactionLoading,
    batchTransactionPage,
    batchTransactionTotal,
    batchTransactionHasNext,
    batchTransactionHasPrev,
    onDragOver,
    onDragLeave,
    onDrop,
    onFileSelect,
    toggleBatch,
    loadBatchTransactions,
    commitImport,
    getStatusBadgeVariant,
    getStatusLabel,
  }
}
