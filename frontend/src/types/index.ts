export interface User {
  id: number
  email: string
  first_name: string
  last_name: string
}

export interface AuthResponse {
  user: User
  access: string
  refresh: string
}

export interface Transaction {
  id: number
  started_at: string
  completed_at: string
  description: string
  amount: number
  fee: number
  currency: string
  transaction_type: string
  state: string
  balance_after: number | null
  category: number | null
  category_name: string | null
  category_color: string | null
  notes: string
  created_at: string
}

export interface TransactionFilters {
  date_from?: string
  date_to?: string
  type?: string
  category?: number
  sign?: 'expense' | 'income'
  search?: string
  page?: number
  page_size?: number
  ordering?: string
}

export interface Category {
  id: number
  name: string
  color: string
  icon: string
  is_system: boolean
}

export interface CategoryRule {
  id: number
  keyword: string
  category: number
  category_name: string
  category_color: string
  priority: number
  created_at: string
}

export interface Budget {
  id: number
  category: number
  category_name: string
  category_color: string
  year: number
  month: number
  amount_limit: number
  current_spent: number
  percentage: number
}

export interface ImportBatch {
  id: number
  filename: string
  imported_at: string
  total_rows: number
  imported_count: number
  skipped_count: number
  error_count: number
  task_id: string | null
  status: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED'
}

export interface StatsSummary {
  total_expenses: number
  total_income: number
  net: number
  transaction_count: number
  period_from: string
  period_to: string
}

export interface CategoryStats {
  category_id: number | null
  category_name: string
  color: string
  total: number
  count: number
}

export interface MonthlyTrend {
  year: number
  month: number
  month_label: string
  expenses: number
  income: number
}

export interface TopMerchant {
  merchant: string
  total: number
  count: number
}

export interface BalancePoint {
  date: string
  balance: number
}

export interface CategoryComparison {
  category: string
  color: string
  current: number
  previous: number
  change_pct: number | null
}

export interface Suggestion {
  type: 'biggest_increase' | 'subscription' | 'spending_peaks' | 'outlier'
  title: string
  message: string
  [key: string]: unknown
}

export interface PaginatedResponse<T> {
  count: number
  next: string | null
  previous: string | null
  results: T[]
}
