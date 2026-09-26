export function LoadingState() {
  return <div className="page-state" role="status"><span className="spinner" aria-hidden="true" />Wczytywanie danych…</div>
}

export function ErrorState({ message, retry }: { message: string; retry?: () => void }) {
  return <div className="page-state page-state--error" role="alert"><strong>Nie udało się wczytać danych</strong><span>{message}</span>{retry && <button type="button" className="button button--secondary" onClick={retry}>Spróbuj ponownie</button>}</div>
}
