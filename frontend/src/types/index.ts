/**
 * TypeScript interfaces and types for the Finance Tracker application.
 *
 * Mirrors the backend API response schemas and provides type safety
 * across all frontend components, stores, and API functions.
 */

/** User profile returned after authentication. */
export interface User {
  /** Unique user identifier. */
  id: number
  /** Email address (used as the login identifier). */
  email: string
  /** User's first name. */
  first_name: string
  /** User's last name. */
  last_name: string
}

/** Response payload from login and registration endpoints. */
export interface AuthResponse {
  /** Authenticated user profile. */
  user: User
  /** JWT access token (short-lived). */
  access: string
  /** JWT refresh token (long-lived, used to obtain new access tokens). */
  refresh: string
}

/** Financial transaction record. */
export interface Transaction {
  /** Unique transaction identifier. */
  id: number
  /** When the transaction started (ISO 8601). */
  started_at: string
  /** When the transaction completed (ISO 8601). */
  completed_at: string
  /** Transaction description or merchant name. */
  description: string
  /** Transaction amount (negative for expenses, positive for income). */
  amount: number
  /** Associated fee amount. */
  fee: number
  /** Currency code (e.g., "EUR"). */
  currency: string
  /** Type of transaction (e.g., "card", "transfer"). */
  transaction_type: string
  /** Current state (e.g., "completed", "pending"). */
  state: string
  /** Account balance after this transaction, or null if unavailable. */
  balance_after: number | null
  /** Foreign key to the assigned category. */
  category: number | null
  /** Denormalised category name for display convenience. */
  category_name: string | null
  /** Denormalised category colour hex code. */
  category_color: string | null
  /** User-added notes. */
  notes: string
  /** Server-side creation timestamp. */
  created_at: string
}

/** Query parameters for filtering the transaction list. */
export interface TransactionFilters {
  /** Start date (inclusive). */
  date_from?: string
  /** End date (inclusive). */
  date_to?: string
  /** Filter by transaction type. */
  type?: string
  /** Filter by category ID. */
  category?: number
  /** Filter by sign: "expense" (negative) or "income" (positive). */
  sign?: 'expense' | 'income'
  /** Free-text search on description. */
  search?: string
  /** Page number for paginated results. */
  page?: number
  /** Number of results per page. */
  page_size?: number
  /** Ordering field (prefix with "-" for descending). */
  ordering?: string
}

/** Expense/income category with visual styling. */
export interface Category {
  /** Unique category identifier. */
  id: number
  /** Display name. */
  name: string
  /** Hex colour code for badges and charts. */
  color: string
  /** Icon identifier for UI display. */
  icon: string
  /** True if this is a built-in system category (not user-editable). */
  is_system: boolean
}

/** Keyword-based rule for automatic transaction categorisation. */
export interface CategoryRule {
  /** Unique rule identifier. */
  id: number
  /** Keyword to match against transaction descriptions. */
  keyword: string
  /** Target category ID to assign on match. */
  category: number
  /** Denormalised category name. */
  category_name: string
  /** Denormalised category colour. */
  category_color: string
  /** Evaluation priority (lower number = higher priority). */
  priority: number
  /** Rule creation timestamp. */
  created_at: string
}

/** Monthly spending budget for a specific category. */
export interface Budget {
  /** Unique budget identifier. */
  id: number
  /** Target category ID. */
  category: number
  /** Denormalised category name. */
  category_name: string
  /** Denormalised category colour. */
  category_color: string
  /** Budget year. */
  year: number
  /** Budget month (1-12). */
  month: number
  /** Maximum spending amount allowed. */
  amount_limit: number
  /** Amount already spent in the current month (computed by backend). */
  current_spent: number
  /** Percentage of the budget consumed (0-100+). */
  percentage: number
}

/** Result of a file import operation. */
export interface ImportBatch {
  /** Unique import batch identifier. */
  id: number
  /** Original uploaded filename. */
  filename: string
  /** Import completion timestamp. */
  imported_at: string
  /** Total rows found in the uploaded file. */
  total_rows: number
  /** Number of successfully imported transactions. */
  imported_count: number
  /** Number of rows skipped (duplicates or errors). */
  skipped_count: number
  /** Number of rows that caused errors. */
  error_count: number
  /** Celery task ID for async imports, or null for sync. */
  task_id: string | null
  /** Current processing status. */
  status: 'PENDING' | 'PROCESSING' | 'COMPLETED' | 'FAILED'
}

/** Summary statistics for a given time period. */
export interface StatsSummary {
  /** Total expenses (absolute value). */
  total_expenses: number
  /** Total income (absolute value). */
  total_income: number
  /** Net balance (income minus expenses). */
  net: number
  /** Number of transactions in the period. */
  transaction_count: number
  /** Period start date. */
  period_from: string
  /** Period end date. */
  end_date: string
}

/** Spending breakdown by category. */
export interface CategoryStats {
  /** Category ID, or null for uncategorised transactions. */
  category_id: number | null
  /** Display name of the category. */
  category_name: string
  /** Category colour hex code. */
  color: string
  /** Total spending in this category. */
  total: number
  /** Number of transactions in this category. */
  count: number
}

/** Monthly income vs. expense trend data point. */
export interface MonthlyTrend {
  /** Year. */
  year: number
  /** Month number (1-12). */
  month: number
  /** Localised month name (e.g., "Gennaio"). */
  month_label: string
  /** Total expenses for the month. */
  expenses: number
  /** Total income for the month. */
  income: number
}

/** Top merchant (by spending description). */
export interface TopMerchant {
  /** Merchant or description label. */
  merchant: string
  /** Total spending with this merchant. */
  total: number
  /** Number of transactions. */
  count: number
}

/** Running balance data point for the balance chart. */
export interface BalancePoint {
  /** Date of the balance point. */
  date: string
  /** Cumulative balance at this date. */
  balance: number
}

/** Category spending comparison between two periods. */
export interface CategoryComparison {
  /** Category name. */
  category: string
  /** Category colour. */
  color: string
  /** Spending in the current period. */
  current: number
  /** Spending in the previous period. */
  previous: number
  /** Percentage change, or null if not calculable. */
  change_pct: number | null
}

/** AI-generated spending insight or anomaly suggestion. */
export interface Suggestion {
  /** Suggestion type for icon/category mapping. */
  type: 'biggest_increase' | 'subscription' | 'spending_peaks' | 'outlier'
  /** Short title displayed in the suggestion card. */
  title: string
  /** Detailed explanation message. */
  message: string
  /** Additional dynamic properties from the AI response. */
  [key: string]: unknown
}

/** Paginated API response wrapper (Django REST Framework format). */
export interface PaginatedResponse<T> {
  /** Total number of items across all pages. */
  count: number
  /** URL of the next page, or null if on the last page. */
  next: string | null
  /** URL of the previous page, or null if on the first page. */
  previous: string | null
  /** Items on the current page. */
  results: T[]
}
