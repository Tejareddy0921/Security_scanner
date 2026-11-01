import '../style/components.css'

const links = [
  { id: 'dashboard', label: 'Overview', icon: '◫' },
  { id: 'scan', label: 'Check a message', icon: '⌕' },
  { id: 'history', label: 'Scan history', icon: '◷' },
  { id: 'profile', label: 'My profile', icon: '○' },
]

export default function Sidebar({ activePage, onNavigate }) {
  return (
    <aside className="sidebar">
      <button className="brand" type="button" onClick={() => onNavigate('dashboard')} aria-label="ScamGuard home">
        <span className="brand-mark">S</span>
        <span>scamguard<span className="brand-period">.</span></span>
      </button>
      <div className="sidebar-label">WORKSPACE</div>
      <nav className="side-nav" aria-label="Main navigation">
        {links.map((link) => (
          <button
            className={`nav-link${activePage === link.id ? ' is-active' : ''}`}
            key={link.id}
            type="button"
            onClick={() => onNavigate(link.id)}
            aria-current={activePage === link.id ? 'page' : undefined}
          >
            <span className="nav-icon" aria-hidden="true">{link.icon}</span>{link.label}
          </button>
        ))}
      </nav>
      <div className="sidebar-tip">
        <span className="tip-icon" aria-hidden="true">✳</span>
        <strong>Stay one step ahead</strong>
        <p>Pause before you click. A quick check can make all the difference.</p>
      </div>
      <div className="sidebar-foot">PRIVATE BY DESIGN <span>•</span> FREE TO USE</div>
    </aside>
  )
}
