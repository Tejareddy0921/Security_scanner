import '../style/components.css'

export default function Navbar({ user, onLogout }) {
  const initials = user?.name?.trim().split(/\s+/).slice(0, 2).map((part) => part[0]).join('').toUpperCase() || 'U'

  return (
    <header className="topbar">
      <div className="topbar-crumb"><span className="status-dot" /> Your personal safety space</div>
      <div className="topbar-user">
        <div className="user-avatar" aria-hidden="true">{initials}</div>
        <div className="user-copy"><strong>{user?.name}</strong><span>Personal account</span></div>
        <button type="button" className="logout-button" onClick={onLogout}>Sign out</button>
      </div>
    </header>
  )
}
