import { api } from './client'
import type { Suggestion } from '@/types'

export const suggestionsApi = {
  list: () => api.get<Suggestion[]>('/suggestions/'),
}
