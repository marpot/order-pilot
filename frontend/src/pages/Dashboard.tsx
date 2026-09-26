import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { api } from '../api'
import { OrderTable } from '../components/OrderTable'
import { ErrorState, LoadingState } from '../components/PageState'
import type { DashboardStats } from '../types'

export function Dashboard() {
  const [stats, setStats] = useState<DashboardStats | null>(null)
  const [error, setError] = useState('')
  const load = () => {
    setError('')
    api.getStats().then(setStats).catch((err: Error) => setError(err.message))
  }
  useEffect(load, [])

  if (error) return <ErrorState message={error} retry={load} />
  if (!stats) return <LoadingState />

  return (
    <div className="page">
      <div className="page-heading">
        <div><span className="eyebrow">Przegląd operacyjny</span><h1>Dzień dobry</h1><p>Zobacz, które zamówienia wymagają dziś Twojej uwagi.</p></div>
        <Link className="button button--primary" to="/import"><span>＋</span> Importuj zamówienie</Link>
      </div>
      <section className="metrics-grid">
        <div className="metric-card metric-card--total"><span>Wszystkie zamówienia</span><strong>{stats.total}</strong><small>Łącznie w systemie</small></div>
        <div className="metric-card metric-card--new"><span>Nowe</span><strong>{stats.new}</strong><small>Oczekują na obsługę</small></div>
        <div className="metric-card metric-card--review"><span>Do weryfikacji</span><strong>{stats.needs_review}</strong><small>Wymagają sprawdzenia</small></div>
        <div className="metric-card metric-card--approved"><span>Zatwierdzone</span><strong>{stats.approved}</strong><small>Gotowe do realizacji</small></div>
      </section>
      <section className="panel">
        <div className="panel__heading"><div><h2>Ostatnie zamówienia</h2><p>Najnowsza aktywność w systemie</p></div><Link to="/orders" className="text-link">Zobacz wszystkie <span>→</span></Link></div>
        <OrderTable orders={stats.recent_orders} compact />
      </section>
    </div>
  )
}

