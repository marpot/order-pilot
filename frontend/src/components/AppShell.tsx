import type { ReactNode } from 'react'
import { NavLink, useLocation } from 'react-router-dom'

const navigation = [
  { to: '/', label: 'Pulpit', icon: 'grid' },
  { to: '/orders', label: 'Zamówienia', icon: 'orders' },
  { to: '/import', label: 'Importuj zamówienie', icon: 'plus' },
]

function Icon({ name }: { name: string }) {
  if (name === 'grid') {
    return <svg aria-hidden="true" viewBox="0 0 24 24"><rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><rect x="14" y="14" width="7" height="7" rx="1"/></svg>
  }
  if (name === 'orders') {
    return <svg aria-hidden="true" viewBox="0 0 24 24"><path d="M7 3h10v4H7zM5 5H3v16h18V5h-2M8 12h8M8 16h5"/></svg>
  }
  return <svg aria-hidden="true" viewBox="0 0 24 24"><path d="M12 5v14M5 12h14"/></svg>
}

export function AppShell({ children }: { children: ReactNode }) {
  const location = useLocation()
  const active = navigation.find((item) => item.to === '/' ? location.pathname === '/' : location.pathname.startsWith(item.to))

  return (
    <div className="app-shell">
      <a className="skip-link" href="#main-content">Przejdź do treści</a>
      <aside className="sidebar">
        <div className="brand">
          <div className="brand__mark">OP</div>
          <div><strong>OrderPilot</strong><span>Intake workspace</span></div>
        </div>
        <nav className="nav" aria-label="Główna nawigacja">
          <span className="nav__label">Przestrzeń robocza</span>
          {navigation.map((item) => (
            <NavLink key={item.to} to={item.to} end={item.to === '/'} className={({ isActive }) => isActive ? 'nav__item active' : 'nav__item'}>
              <Icon name={item.icon} />
              {item.label}
            </NavLink>
          ))}
        </nav>
        <div className="sidebar__footer">
          <span className="system-dot" />
          <div><strong>System działa</strong><span>Środowisko demo</span></div>
        </div>
      </aside>
      <div className="workspace">
        <header className="topbar">
          <div><span className="topbar__eyebrow">OrderPilot</span><strong>{active?.label ?? 'Zamówienie'}</strong></div>
          <div className="operator"><span>MK</span><div><strong>Operator</strong><small>Panel operacyjny</small></div></div>
        </header>
        <main className="main-content" id="main-content" tabIndex={-1}>{children}</main>
      </div>
    </div>
  )
}
