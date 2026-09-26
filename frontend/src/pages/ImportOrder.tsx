import { DragEvent, FormEvent, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { api } from '../api'

const DEMO_TEXT = `Dzień dobry,

proszę o zamówienie:

20 x FILTR-X100
5 x POMPA-P20
10 x ZAWÓR-Z15

Dostawa do:
ABC Sp. z o.o.
ul. Przemysłowa 15
40-001 Katowice

Prosimy o dostawę do 30.09.2026.

Pozdrawiam
Jan Kowalski`

export function ImportOrder() {
  const [mode, setMode] = useState<'text' | 'file'>('text')
  const [content, setContent] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [dragging, setDragging] = useState(false)
  const [processing, setProcessing] = useState(false)
  const [error, setError] = useState('')
  const navigate = useNavigate()
  const fileInput = useRef<HTMLInputElement>(null)

  const submit = async (event: FormEvent) => {
    event.preventDefault()
    if (mode === 'text' && !content.trim()) return
    if (mode === 'file' && !file) return
    setProcessing(true)
    setError('')
    try {
      const order = mode === 'text' ? await api.importText(content) : await api.importFile(file!)
      navigate(`/orders/${order.id}`, { state: { imported: true } })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Nie udało się przetworzyć tekstu')
      setProcessing(false)
    }
  }

  const selectFile = (selected?: File) => {
    if (!selected) return
    setError('')
    setFile(selected)
  }

  const dropFile = (event: DragEvent<HTMLDivElement>) => {
    event.preventDefault()
    setDragging(false)
    selectFile(event.dataTransfer.files[0])
  }

  return (
    <div className="page page--narrow">
      <div className="page-heading"><div><span className="eyebrow">Nowe zamówienie</span><h1>Importuj treść zamówienia</h1><p>Wklej wiadomość od klienta. OrderPilot rozpozna pozycje i przygotuje zamówienie do weryfikacji.</p></div></div>
      <section className="panel import-panel">
        <div className="import-tabs" role="tablist" aria-label="Format importu">
          <button type="button" role="tab" aria-selected={mode === 'text'} className={mode === 'text' ? 'active' : ''} onClick={() => setMode('text')}><span>01</span> Tekst / e-mail</button>
          <button type="button" role="tab" aria-selected={mode === 'file'} className={mode === 'file' ? 'active' : ''} onClick={() => setMode('file')}><span>02</span> CSV / XLSX / PDF</button>
        </div>
        <div className="import-panel__header"><div className="mail-icon">{mode === 'text' ? '✉' : '⇧'}</div><div><h2>{mode === 'text' ? 'Wklej e-mail lub treść zamówienia' : 'Prześlij dokument zamówienia'}</h2><p>{mode === 'text' ? 'System rozpozna pozycje, klienta, adres i termin dostawy.' : 'Maksymalny rozmiar pliku: 5 MB. Obsługiwane formaty: CSV, XLSX i tekstowy PDF.'}</p></div></div>
        <form onSubmit={submit}>
          {mode === 'text' ? <>
            <div className="field-heading"><label htmlFor="order-content">Treść wiadomości</label><button type="button" className="text-button" onClick={() => setContent(DEMO_TEXT)}>Wstaw przykład</button></div>
            <textarea id="order-content" value={content} onChange={(event) => setContent(event.target.value)} placeholder="Dzień dobry,&#10;&#10;proszę o zamówienie:&#10;20 x FILTR-X100&#10;..." rows={18} />
          </> : <>
            <input ref={fileInput} className="sr-only" id="order-file" type="file" accept=".csv,.xlsx,.pdf" onChange={(event) => selectFile(event.target.files?.[0])} />
            <div className={`file-drop${dragging ? ' file-drop--active' : ''}${file ? ' file-drop--selected' : ''}`} onDragEnter={() => setDragging(true)} onDragLeave={() => setDragging(false)} onDragOver={(event) => event.preventDefault()} onDrop={dropFile}>
              <div className="file-drop__icon" aria-hidden="true">{file ? '✓' : '⇧'}</div>
              {file ? <><strong>{file.name}</strong><span>{formatFileSize(file.size)}</span><button type="button" className="text-button" onClick={() => fileInput.current?.click()}>Wybierz inny plik</button></> : <><strong>Przeciągnij plik tutaj</strong><span>lub wybierz go z dysku</span><button type="button" className="button button--secondary" onClick={() => fileInput.current?.click()}>Wybierz plik</button></>}
            </div>
            <div className="format-help"><strong>Format CSV/XLSX</strong><span>Kolumny wymagane: <code>sku</code>, <code>quantity</code>. Dane zamówienia: <code>customer</code>, <code>delivery_address</code>, <code>delivery_date</code>.</span></div>
          </>}
          <div className="form-note"><span>ⓘ</span> Brakujące dane nie zostaną wymyślone — zamówienie trafi do weryfikacji.</div>
          {error && <div className="inline-error" role="alert">{error}</div>}
          <div className="form-actions"><button className="button button--primary button--large" disabled={(mode === 'text' ? !content.trim() : !file) || processing}>{processing ? <><span className="spinner spinner--small" aria-hidden="true" />Przetwarzanie…</> : <>Przetwórz zamówienie <span aria-hidden="true">→</span></>}</button></div>
        </form>
      </section>
    </div>
  )
}

function formatFileSize(size: number): string {
  return size < 1024 * 1024 ? `${Math.ceil(size / 1024)} KB` : `${(size / 1024 / 1024).toFixed(1)} MB`
}
