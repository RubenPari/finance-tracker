import { api } from './client'
import type { ImportBatch, PaginatedResponse, Transaction, TransactionFilters } from '@/types'

export const transactionsApi = {
  list: (filters?: TransactionFilters) =>
    api.get<PaginatedResponse<Transaction>>('/transactions/', { params: filters }),
  get: (id: number) => api.get<Transaction>(`/transactions/${id}/`),
  update: (id: number, data: Partial<Transaction>) => api.patch<Transaction>(`/transactions/${id}/update/`, data),
  delete: (id: number) => api.delete(`/transactions/${id}/delete/`),
  import: (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post<ImportBatch>('/transactions/import/', formData, {
      headers: { 'Content-Type': 'multipart/form-data' },
    })
  },
  importHistory: () => api.get<ImportBatch[]>('/transactions/import/history/'),
  importDetail: (id: number) => api.get<ImportBatch>(`/transactions/import/${id}/`),
  batchTransactions: (batchId: number, filters?: TransactionFilters) =>
    api.get<PaginatedResponse<Transaction>>(`/transactions/import/${batchId}/transactions/`, {
      params: filters,
    }),
  commitImport: (batchId: number) => api.post<{ message: string }>(`/transactions/import/${batchId}/commit/`),
}
