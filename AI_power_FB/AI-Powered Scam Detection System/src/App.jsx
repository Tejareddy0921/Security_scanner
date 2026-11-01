import { useEffect, useState } from 'react'
import Dashboard from './pages/Dashboard.jsx'
import History from './pages/History.jsx'
import Login from './pages/Login.jsx'
import Profile from './pages/Profile.jsx'
import Register from './pages/Register.jsx'
import ScamInputPage from './pages/ScamInput.jsx'
import Navbar from './components/Navbar.jsx'
import ProtectedRoute from './components/ProtectedRoute.jsx'
import Sidebar from './components/Sidebar.jsx'
import { useAuth } from './hooks/useAuth.js'
import './style/layout.css'

const knownPages = new Set(['dashboard', 'scan', 'history', 'profile', 'login', 'register'])


function readPage() {
  const page = window.location.pathname.replace(/^\/+|\/+$/g, '').toLowerCase()
  return knownPages.has(page) ? page : 'dashboard'
}

export default function App() {
  const { user, token, logout, isInitializing, sessionRestoreError, restoreSession } = useAuth()
  const [page, setPage] = useState(readPage)

  useEffect(() => {
    const syncPage = () => setPage(readPage())
    window.addEventListener('popstate', syncPage)
    return () => window.removeEventListener('popstate', syncPage)
  }, [])

  const activePage = page === 'login' || page === 'register' ? 'dashboard' : page

  function navigate(nextPage) {
    const normalizedPage = knownPages.has(nextPage) ? nextPage : 'dashboard'
    window.history.pushState(null, '', `/${normalizedPage}`)
    setPage(normalizedPage)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  if (isInitializing) {
    return <main className="auth-page"><section className="auth-card" role="status">Restoring your session…</section></main>
  }

  if (sessionRestoreError) {
    return (
      <main className="auth-page">
        <section className="auth-card">
          <h1>Couldn’t restore your session</h1>
          <p className="form-error" role="alert">{sessionRestoreError}</p>
          <button className="button button-primary auth-submit" type="button" onClick={restoreSession}>Try again</button>
          <button className="text-button" type="button" onClick={() => { logout(); navigate('login') }}>Sign in instead</button>
        </section>
      </main>
    )
  }

  if (!user) {
    return page === 'register' ? <Register onNavigate={navigate} /> : <Login onNavigate={navigate} />
  }

  let currentPage
  if (activePage === 'scan') currentPage = <ScamInputPage token={token} />
  else if (activePage === 'history') currentPage = <History token={token} />
  else if (activePage === 'profile') currentPage = <Profile user={user} />
  else currentPage = <Dashboard onNavigate={navigate} user={user} token={token} />

  return (
    <ProtectedRoute isAuthenticated={Boolean(user)} fallback={<Login onNavigate={navigate} />}>
      <div className="app-layout">
        <Sidebar activePage={activePage} onNavigate={navigate} />
        <div className="main-column">
          <Navbar user={user} onLogout={() => { logout(); navigate('login') }} />
          <main className="page-content">{currentPage}</main>
        </div>
      </div>
    </ProtectedRoute>
  )
}
