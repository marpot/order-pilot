import { ChangeEvent, FormEvent, useEffect, useState } from 'react'
import { Link, useLocation, useNavigate, useParams } from 'react-router-dom'
import { api, formatDate, sourceLabels } from '../api'
import { ErrorState, LoadingState } from '../components/PageState'
import { StatusBadge } from '../components/StatusBadge'
import type { Order, OrderHistory, OrderHistoryAction, OrderItem } from '../types'

type EditableOrder = Pick<Order, 'customer_name' | 'customer_email' | 'customer_tax_id' | 'delivery_address' | 'delivery_date' | 'items'>

export function OrderDetails() {
  const { id } = useParams()
  const location = useLocation()
  const navigate = useNavigate()
  const [order, setOrder] = useState<Order | null>(null)
  const [draft, setDraft] = useState<EditableOrder | null>(null)
  const [history, setHistory] = useState<OrderHistory[]>([])
  const [editing, setEditing] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [notice, setNotice] = useState(location.state?.imported ? 'Zamówienie zostało przetworzone. Sprawdź dane przed zatwierdzeniem.' : '')

  const load = () => {
    if (!id) return
    setError('')
    Promise.all([api.getOrder(id), api.getOrderHistory(id)])
      .then(([data, historyData]) => { setOrder(data); setDraft(toDraft(data)); setHistory(historyData) })
      .catch((err: Error) => setError(err.message))
  }
  useEffect(load, [id])

  if (error && !order) return <ErrorState message={error} retry={load} />
  if (!order || !draft) return <LoadingState />
  const isTerminal = order.status === 'APPROVED' || order.status === 'REJECTED'

  const setField = (field: keyof Omit<EditableOrder, 'items'>, value: string) => setDraft({ ...draft, [field]: value || null })
  const updateItem = (index: number, field: keyof OrderItem, value: string | number) => {
    const items = draft.items.map((item, itemIndex) => itemIndex === index ? { ...item, [field]: value } : item)
    setDraft({ ...draft, items })
  }
  const refreshHistory = async () => setHistory(await api.getOrderHistory(order.id))
  const save = async (event: FormEvent) => {
    event.preventDefault()
    setBusy(true); setError('')
    try {
      const updated = await api.updateOrder(order.id, { ...draft, items: draft.items.map(({ sku, product_name, quantity, unit }) => ({ sku, product_name, quantity, unit })) } as Partial<Order>)
      await refreshHistory()
      setOrder(updated); setDraft(toDraft(updated)); setEditing(false); setNotice('Zmiany zostały zapisane.')
    } catch (err) { setError(err instanceof Error ? err.message : 'Nie udało się zapisać zmian') }
    finally { setBusy(false) }
  }
  const changeStatus = async (action: 'approve' | 'reject') => {
    setBusy(true); setError('')
    try {
      const updated = await api.setStatus(order.id, action)
      await refreshHistory()
      setOrder(updated); setDraft(toDraft(updated)); setNotice(action === 'approve' ? 'Zamówienie zostało zatwierdzone.' : 'Zamówienie zostało odrzucone.')
    } catch (err) { setError(err instanceof Error ? err.message : 'Nie udało się zmienić statusu') }
    finally { setBusy(false) }
  }

  return (
    <div className="page">
      <div className="breadcrumb"><Link to="/orders">Zamówienia</Link><span>/</span><strong>OP-{String(order.id).padStart(4, '0')}</strong></div>
      <div className="detail-heading">
        <div><div className="detail-heading__title"><h1>Zamówienie OP-{String(order.id).padStart(4, '0')}</h1><StatusBadge status={order.status} /></div><p>Utworzono {formatDate(order.created_at, true)} · Źródło: {sourceLabels[order.source]}</p></div>
        <div className="detail-actions">
          {editing ? <><button className="button button--secondary" onClick={() => { setDraft(toDraft(order)); setEditing(false) }} disabled={busy}>Anuluj</button><button className="button button--primary" type="submit" form="order-form" disabled={busy}>{busy ? 'Zapisywanie…' : 'Zapisz zmiany'}</button></> : <button className="button button--secondary" onClick={() => setEditing(true)}>✎ Edytuj dane</button>}
        </div>
      </div>
      {notice && <div className="notice"><span>✓</span>{notice}<button onClick={() => setNotice('')}>×</button></div>}
      {error && <div className="inline-error">{error}</div>}
      <form id="order-form" onSubmit={save} className="detail-grid">
        <div className="detail-main">
          <section className="panel detail-card">
            <div className="section-title"><span className="section-icon">▣</span><div><h2>Dane klienta i dostawy</h2><p>Informacje rozpoznane z treści zamówienia</p></div></div>
            <div className="form-grid">
              <Field label="Nazwa klienta" value={draft.customer_name ?? ''} editing={editing} onChange={(value) => setField('customer_name', value)} />
              <Field label="Adres e-mail" value={draft.customer_email ?? ''} editing={editing} onChange={(value) => setField('customer_email', value)} type="email" />
              <Field label="NIP" value={draft.customer_tax_id ?? ''} editing={editing} onChange={(value) => setField('customer_tax_id', value)} />
              <Field label="Data dostawy" value={draft.delivery_date ?? ''} editing={editing} onChange={(value) => setField('delivery_date', value)} type="date" />
              <Field label="Adres dostawy" value={draft.delivery_address ?? ''} editing={editing} onChange={(value) => setField('delivery_address', value)} multiline wide />
            </div>
          </section>
          <section className="panel detail-card">
            <div className="section-title"><span className="section-icon">≡</span><div><h2>Pozycje zamówienia</h2><p>{draft.items.length} {draft.items.length === 1 ? 'pozycja' : 'pozycje'} w zamówieniu</p></div></div>
            <div className="items-table-wrap"><table className="items-table"><thead><tr><th>SKU</th><th>Nazwa produktu</th><th>Ilość</th><th>Jednostka</th>{editing && <th />}</tr></thead><tbody>
              {draft.items.map((item, index) => <tr key={item.id ?? index}>
                <td>{editing ? <input value={item.sku} required onChange={(event) => updateItem(index, 'sku', event.target.value)} /> : <strong>{item.sku}</strong>}</td>
                <td>{editing ? <input value={item.product_name ?? ''} onChange={(event) => updateItem(index, 'product_name', event.target.value)} /> : item.product_name || '—'}</td>
                <td>{editing ? <input className="quantity-input" type="number" min="1" value={item.quantity} onChange={(event) => updateItem(index, 'quantity', Number(event.target.value))} /> : <strong>{item.quantity}</strong>}</td>
                <td>{editing ? <input className="unit-input" value={item.unit} onChange={(event) => updateItem(index, 'unit', event.target.value)} /> : item.unit}</td>
                {editing && <td><button type="button" className="remove-button" onClick={() => setDraft({ ...draft, items: draft.items.filter((_, itemIndex) => itemIndex !== index) })} aria-label="Usuń pozycję">×</button></td>}
              </tr>)}
              {!draft.items.length && <tr><td colSpan={5} className="empty-row">Brak pozycji — dodaj co najmniej jedną przed zatwierdzeniem.</td></tr>}
            </tbody></table></div>
            {editing && <button type="button" className="add-row-button" onClick={() => setDraft({ ...draft, items: [...draft.items, { sku: '', product_name: '', quantity: 1, unit: 'szt.' }] })}>＋ Dodaj pozycję</button>}
          </section>
          <section className="panel detail-card">
            <div className="section-title"><span className="section-icon">↳</span><div><h2>Oryginalna treść</h2><p>Materiał źródłowy zachowany do weryfikacji</p></div></div>
            <pre className="original-content">{order.original_content || 'Brak treści źródłowej.'}</pre>
          </section>
          <section className="panel detail-card">
            <div className="section-title"><span className="section-icon">◷</span><div><h2>Historia zamówienia</h2><p>Chronologiczny zapis operacji wykonanych na zamówieniu</p></div></div>
            <OrderHistoryTimeline entries={history} />
          </section>
        </div>
        <aside className="detail-side">
          <section className="panel decision-card"><h2>Decyzja</h2><p>{isTerminal ? 'To zamówienie zakończyło proces decyzyjny. Dalsza zmiana statusu jest zablokowana.' : 'Po sprawdzeniu danych zatwierdź zamówienie do realizacji albo je odrzuć.'}</p><button type="button" className="button button--approve" disabled={busy || isTerminal} onClick={() => changeStatus('approve')}>✓ Zatwierdź zamówienie</button><button type="button" className="button button--reject" disabled={busy || isTerminal} onClick={() => changeStatus('reject')}>Odrzuć zamówienie</button></section>
          <section className="panel meta-card"><h3>Informacje</h3><dl><div><dt>Źródło</dt><dd>{sourceLabels[order.source]}</dd></div><div><dt>Utworzono</dt><dd>{formatDate(order.created_at, true)}</dd></div><div><dt>Ostatnia zmiana</dt><dd>{formatDate(order.updated_at, true)}</dd></div></dl></section>
          <button type="button" className="back-button" onClick={() => navigate('/orders')}>← Wróć do listy</button>
        </aside>
      </form>
    </div>
  )
}

function toDraft(order: Order): EditableOrder {
  return { customer_name: order.customer_name, customer_email: order.customer_email, customer_tax_id: order.customer_tax_id, delivery_address: order.delivery_address, delivery_date: order.delivery_date, items: order.items.map((item) => ({ ...item })) }
}

function Field({ label, value, editing, onChange, type = 'text', multiline = false, wide = false }: { label: string; value: string; editing: boolean; onChange: (value: string) => void; type?: string; multiline?: boolean; wide?: boolean }) {
  const handleChange = (event: ChangeEvent<HTMLInputElement | HTMLTextAreaElement>) => onChange(event.target.value)
  return <div className={`detail-field${wide ? ' detail-field--wide' : ''}`}><label>{label}</label>{editing ? (multiline ? <textarea rows={3} value={value} onChange={handleChange} /> : <input type={type} value={value} onChange={handleChange} />) : <div className={value ? '' : 'muted'}>{type === 'date' && value ? formatDate(value) : value || 'Nie podano'}</div>}</div>
}

const historyActionLabels: Record<OrderHistoryAction, string> = {
  IMPORTED: 'Zaimportowano',
  EDITED: 'Edytowano',
  APPROVED: 'Zatwierdzono',
  REJECTED: 'Odrzucono',
}

function OrderHistoryTimeline({ entries }: { entries: OrderHistory[] }) {
  if (!entries.length) return <div className="history-empty">Brak zarejestrowanych zdarzeń dla tego zamówienia.</div>

  return <ol className="history-timeline">
    {entries.map((entry) => <li key={entry.id} className={`history-event history-event--${entry.action.toLowerCase()}`}>
      <span className="history-event__marker" aria-hidden="true" />
      <div className="history-event__content">
        <strong>{historyActionLabels[entry.action]}</strong>
        <time dateTime={entry.timestamp}>{formatDate(entry.timestamp, true)}</time>
        {entry.details && <small>{formatHistoryDetails(entry.details)}</small>}
      </div>
    </li>)}
  </ol>
}

function formatHistoryDetails(details: string): string {
  if (details.startsWith('Source: ')) {
    return details.replace('Source: EMAIL', 'Źródło: e-mail').replace('Source: CSV', 'Źródło: CSV').replace('Source: XLSX', 'Źródło: Excel').replace('Source: PDF', 'Źródło: PDF')
  }
  if (!details.startsWith('Changed fields: ')) return details
  const labels: Record<string, string> = {
    customer_name: 'nazwa klienta', customer_email: 'adres e-mail', customer_tax_id: 'NIP',
    delivery_address: 'adres dostawy', delivery_date: 'data dostawy', items: 'pozycje zamówienia',
    source: 'źródło', status: 'status', original_content: 'treść źródłowa',
  }
  const fields = details.replace('Changed fields: ', '').split(', ').map((field) => labels[field] ?? field)
  return `Zmieniono: ${fields.join(', ')}`
}
