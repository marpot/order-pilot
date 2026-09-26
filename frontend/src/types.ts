export type OrderStatus = 'NEW' | 'NEEDS_REVIEW' | 'APPROVED' | 'REJECTED'
export type OrderSource = 'EMAIL' | 'CSV' | 'PDF' | 'XLSX' | 'MANUAL'
export type OrderHistoryAction = 'IMPORTED' | 'EDITED' | 'APPROVED' | 'REJECTED'

export interface OrderItem {
  id?: number
  order_id?: number
  sku: string
  product_name: string | null
  quantity: number
  unit: string
}

export interface Order {
  id: number
  customer_name: string | null
  customer_email: string | null
  customer_tax_id: string | null
  delivery_address: string | null
  delivery_date: string | null
  source: OrderSource
  status: OrderStatus
  original_content: string | null
  created_at: string
  updated_at: string
  items: OrderItem[]
}

export interface OrderHistory {
  id: number
  order_id: number
  action: OrderHistoryAction
  timestamp: string
  details: string | null
}

export interface DashboardStats {
  total: number
  new: number
  needs_review: number
  approved: number
  rejected: number
  recent_orders: Order[]
}
