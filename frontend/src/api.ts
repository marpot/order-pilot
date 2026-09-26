import type { DashboardStats, Order, OrderHistory, OrderStatus } from './types'

const API_URL = (import.meta.env.VITE_API_URL ?? '').replace(/\/$/, '')

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_URL}${path}`, {
    headers: { 'Content-Type': 'application/json', ...options?.headers },
    ...options,
  })
  if (!response.ok) {
    const body = await response.json().catch(() => null)
    const detail = body?.detail
    const message = Array.isArray(detail)
      ? detail.map((issue) => issue.msg).join('. ')
      : typeof detail === 'string' ? detail : 'Nie udało się wykonać operacji'
    throw new Error(message)
  }
  return response.status === 204 ? (undefined as T) : response.json()
}

export const api = {
  getOrders: () => request<Order[]>('/api/orders'),
  getOrder: (id: string | number) => request<Order>(`/api/orders/${id}`),
  getOrderHistory: (id: string | number) => request<OrderHistory[]>(`/api/orders/${id}/history`),
  getStats: () => request<DashboardStats>('/api/dashboard/stats'),
  importText: (content: string) =>
    request<Order>('/api/import/text', { method: 'POST', body: JSON.stringify({ content }) }),
  importFile: (file: File) => {
    const body = new FormData()
    body.append('file', file)
    return request<Order>('/api/import/file', { method: 'POST', body, headers: {} })
  },
  updateOrder: (id: number, payload: Partial<Order>) =>
    request<Order>(`/api/orders/${id}`, { method: 'PATCH', body: JSON.stringify(payload) }),
  setStatus: (id: number, action: 'approve' | 'reject') =>
    request<Order>(`/api/orders/${id}/${action}`, { method: 'POST' }),
}

export const statusLabels: Record<OrderStatus, string> = {
  NEW: 'Nowe',
  NEEDS_REVIEW: 'Do weryfikacji',
  APPROVED: 'Zatwierdzone',
  REJECTED: 'Odrzucone',
}

export const sourceLabels = {
  EMAIL: 'E-mail',
  CSV: 'CSV',
  PDF: 'PDF',
  XLSX: 'Excel',
  MANUAL: 'Ręcznie',
} as const

export function formatDate(value: string | null, includeTime = false): string {
  if (!value) return '—'
  return new Intl.DateTimeFormat('pl-PL', {
    day: '2-digit',
    month: 'short',
    year: 'numeric',
    ...(includeTime ? { hour: '2-digit', minute: '2-digit' } : {}),
  }).format(new Date(value))
}
