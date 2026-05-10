import { api } from './client'
import type { AuthResponse, LoginResponse, User } from '@/types'

export const authApi = {
  login: (email: string, password: string) => api.post<LoginResponse>('/auth/login/', { email, password }),
  register: (data: Record<string, string>) => api.post<AuthResponse>('/auth/register/', data),
  refresh: (refresh: string) => api.post<{ access: string; refresh: string }>('/auth/refresh/', { refresh }),
  logout: (refresh: string) => api.post('/auth/logout/', { refresh }),
  me: () => api.get<User>('/auth/me/'),
}
