export function formatCurrency(v: number): string {
  return new Intl.NumberFormat('it-IT', { style: 'currency', currency: 'EUR' }).format(v)
}

export function formatDate(d: string): string {
  return new Date(d).toLocaleDateString('it-IT', { day: '2-digit', month: 'short', year: 'numeric' })
}

export function formatDateTime(d: string): string {
  return new Date(d).toLocaleString('it-IT')
}
