/**
 * Formatting utility functions for displaying values in the UI.
 *
 * All currency and date formatting uses the Italian locale (`it-IT`)
 * to match the application's target audience.
 */

/**
 * Format a number as a Euro currency string.
 *
 * @param v - Numeric value to format.
 * @returns Formatted string (e.g., "1.234,56 €").
 */
export function formatCurrency(v: number): string {
  return new Intl.NumberFormat('it-IT', { style: 'currency', currency: 'EUR' }).format(v)
}

/**
 * Format an ISO date string into a short Italian date.
 *
 * @param d - ISO 8601 date string.
 * @returns Formatted date (e.g., "15 gen 2024").
 */
export function formatDate(d: string): string {
  return new Date(d).toLocaleDateString('it-IT', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  })
}

/**
 * Format an ISO date string into a full Italian date and time.
 *
 * @param d - ISO 8601 date string.
 * @returns Formatted date-time string.
 */
export function formatDateTime(d: string): string {
  return new Date(d).toLocaleString('it-IT')
}

/**
 * Generate inline CSS styles for a category badge based on its colour.
 *
 * Adjusts opacity levels depending on the current theme (dark/light)
 * by checking the `dark` class on the document root element.
 *
 * @param color - Hex colour code (e.g., "#ff5733").
 * @returns An object with `backgroundColor`, `color`, and `border` styles.
 */
export function categoryBadgeStyle(color: string): Record<string, string> {
  const isDark = document.documentElement.classList.contains('dark')
  return {
    // Lower opacity background in dark mode for better contrast
    backgroundColor: `${color}${isDark ? '30' : '20'}`,
    color,
    border: `1px solid ${color}${isDark ? '40' : '30'}`,
  }
}
