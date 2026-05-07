export function formatCurrency(v: number): string {
  return new Intl.NumberFormat('it-IT', { style: 'currency', currency: 'EUR' }).format(v)
}

export function formatDate(d: string): string {
  return new Date(d).toLocaleDateString('it-IT', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
  })
}

export function formatDateTime(d: string): string {
  return new Date(d).toLocaleString('it-IT')
}

export function categoryBadgeStyle(color: string): Record<string, string> {
  const isDark = document.documentElement.classList.contains('dark')
  return {
    backgroundColor: `${color}${isDark ? '30' : '20'}`,
    color,
    border: `1px solid ${color}${isDark ? '40' : '30'}`,
  }
}
