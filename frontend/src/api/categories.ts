import { api } from './client'
import type { Category, CategoryRule } from '@/types'

export const categoriesApi = {
  list: () => api.get<Category[]>('/categories/'),
  create: (data: Partial<Category>) => api.post<Category>('/categories/create/', data),
  update: (id: number, data: Partial<Category>) => api.patch<Category>(`/categories/${id}/update/`, data),
  delete: (id: number) => api.delete(`/categories/${id}/delete/`),
  rules: () => api.get<CategoryRule[]>('/categories/rules/'),
  createRule: (data: Partial<CategoryRule>) => api.post<CategoryRule>('/categories/rules/create/', data),
  deleteRule: (id: number) => api.delete(`/categories/rules/${id}/delete/`),
}
