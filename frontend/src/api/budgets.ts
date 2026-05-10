import { api } from './client'
import type { Budget } from '@/types'

export const budgetsApi = {
  list: (params?: { year?: number; month?: number }) => api.get<Budget[]>('/budgets/', { params }),
  create: (data: Partial<Budget>) => api.post<Budget>('/budgets/create/', data),
  update: (id: number, data: Partial<Budget>) => api.patch<Budget>(`/budgets/${id}/update/`, data),
  delete: (id: number) => api.delete(`/budgets/${id}/delete/`),
}
