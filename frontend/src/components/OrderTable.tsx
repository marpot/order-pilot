import { Link } from 'react-router-dom'
import { formatDate, sourceLabels } from '../api'
import type { Order } from '../types'
import { StatusBadge } from './StatusBadge'

export function OrderTable({ orders, compact = false }: { orders: Order[]; compact?: boolean }) {
  if (!orders.length) return <div className="empty-state">Brak zamówień do wyświetlenia.</div>

  return (
    <div className="table-wrap">
      <table className="order-table" aria-label="Lista zamówień">
        <thead><tr><th>Numer</th><th>Klient</th><th>Źródło</th>{!compact && <th>Utworzono</th>}<th>Dostawa</th><th>Status</th><th /></tr></thead>
        <tbody>
          {orders.map((order) => (
            <tr key={order.id}>
              <td><span className="order-number">OP-{String(order.id).padStart(4, '0')}</span></td>
              <td><strong>{order.customer_name || 'Nieustalony klient'}</strong><small>{order.items.length} {order.items.length === 1 ? 'pozycja' : 'pozycji'}</small></td>
              <td><span className="source-tag">{sourceLabels[order.source]}</span></td>
              {!compact && <td>{formatDate(order.created_at)}</td>}
              <td>{formatDate(order.delivery_date)}</td>
              <td><StatusBadge status={order.status} /></td>
              <td><Link className="row-link" to={`/orders/${order.id}`} aria-label={`Otwórz zamówienie ${order.id}`}>→</Link></td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  )
}
