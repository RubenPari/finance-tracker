<script setup lang="ts">
import { formatDateTime, formatDate, formatCurrency } from '@/utils/formatters'
import { Card, CardContent } from '@/components/ui/card'
import { Button } from '@/components/ui/button'
import { Badge } from '@/components/ui/badge'
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
import { useImportWorkflow } from '@/composables/useImportWorkflow'

const {
  fileInput,
  dragging,
  uploading,
  committing,
  result,
  error,
  history,
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
} = useImportWorkflow()
</script>

<template>
  <div>
    <h1 class="mb-6 text-2xl font-bold tracking-tight">Importa XLSX</h1>
    <div
      v-if="error"
      class="mb-4 rounded-lg border border-destructive/50 bg-destructive/10 px-4 py-3 text-sm text-destructive"
    >
      {{ error }}
    </div>

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
        </CardContent>
      </Card>
    </template>

    <template v-if="result && result.status === 'PROCESSING'">
      <Card>
        <CardContent class="flex flex-col items-center py-12">
          <Loader2 class="mb-4 size-10 animate-spin text-primary" />
          <p class="font-medium">Elaborazione in corso...</p>
          <p class="mt-1 text-sm text-muted-foreground">Importazione di {{ result.filename }}</p>
        </CardContent>
      </Card>
    </template>

    <template v-if="result && (result.status === 'COMPLETED' || result.status === 'STAGED')">
      <Card>
        <CardContent class="pt-6">
          <div class="mb-6 text-center">
            <component
              :is="result.status === 'STAGED' ? FileSpreadsheet : CheckCircle2"
              class="mx-auto size-10"
              :class="result.status === 'STAGED' ? 'text-warning' : 'text-income'"
            />
            <h2 class="mt-2 text-xl font-semibold">
              {{ result.status === 'STAGED' ? 'Import pronto per la conferma' : 'Import completato!' }}
            </h2>
            <p v-if="result.status === 'STAGED'" class="mt-1 text-sm text-muted-foreground">
              Le transazioni sono in staging. Conferma per salvarle definitivamente.
            </p>
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
            <Button
              v-if="result.status === 'STAGED'"
              :disabled="committing"
              @click="commitImport(result.id)"
            >
              <Loader2 v-if="committing" class="mr-2 size-4 animate-spin" />
              Conferma importazione
            </Button>
            <RouterLink to="/transactions">
              <Button :variant="result.status === 'STAGED' ? 'outline' : 'default'">Vedi transazioni</Button>
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