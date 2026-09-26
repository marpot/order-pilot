import { useEffect, useMemo, useState } from 'react'
import { Link } from 'react-router-dom'
import { api, statusLabels } from '../api'
import { OrderTable } from '../components/OrderTable'
import { ErrorState, LoadingState } from '../components/PageState'
import type { Order, OrderStatus } from '../types'

type Filter = 'ALL' | OrderStatus

export function Orders() {
  const [orders, setOrders] = useState<Order[] | null>(null)
  const [filter, setFilter] = useState<Filter>('ALL')
  const [query, setQuery] = useState('')
  const [error, setError] = useState('')
  const load = () => {
    setError('')
    api.getOrders().then(setOrders).catch((err: Error) => setError(err.message))
  }
  useEffect(load, [])
  const filtered = useMemo(() => (orders ?? []).filter((order) => {
    const matchesStatus = filter === 'ALL' || order.status === filter
    const haystack = `${order.customer_name ?? ''} ${order.id} ${order.items.map((item) => item.sku).join(' ')}`.toLowerCase()
    return matchesStatus && haystack.includes(query.toLowerCase())
  }), [orders, filter, query])

  if (error) return <ErrorState message={error} retry={load} />
  if (!orders) return <LoadingState />

  return (
    <div className="page">
      <div className="page-heading">
        <div><span className="eyebrow">Rejestr zamówień</span><h1>Zamówienia</h1><p>Przeglądaj i obsługuj wszystkie zarejestrowane zamówienia.</p></div>
        <Link className="button button--primary" to="/import"><span>＋</span> Importuj zamówienie</Link>
      </div>
      <section className="panel">
        <div className="toolbar">
          <label className="search"><span aria-hidden="true">⌕</span><span className="sr-only">Szukaj zamówień</span><input value={query} onChange={(event) => setQuery(event.target.value)} placeholder="Szukaj klienta, numeru lub SKU…" /></label>
          <div className="filter-tabs">
            <button type="button" aria-pressed={filter === 'ALL'} className={filter === 'ALL' ? 'active' : ''} onClick={() => setFilter('ALL')}>Wszystkie <i>{orders.length}</i></button>
            {(['NEW', 'NEEDS_REVIEW', 'APPROVED', 'REJECTED'] as OrderStatus[]).map((status) => (
              <button type="button" aria-pressed={filter === status} key={status} className={filter === status ? 'active' : ''} onClick={() => setFilter(status)}>{statusLabels[status]} <i>{orders.filter((order) => order.status === status).length}</i></button>
            ))}
          </div>
        </div>
        <OrderTable orders={filtered} />
      </section>
    </div>
  )
}
