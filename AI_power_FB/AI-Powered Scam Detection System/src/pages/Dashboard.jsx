import { useEffect, useState } from 'react'
import { getScanHistory } from '../services/scamService.js'
import '../style/pages/dashboard.css'

export default function Dashboard({ onNavigate, user, token }) {
  const [history, setHistory] = useState([])
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const [reloadCount, setReloadCount] = useState(0)

  useEffect(() => {
    let isCurrent = true
    setHistory([])
    setError('')
    setIsLoading(true)
    getScanHistory(token)
      .then((items) => { if (isCurrent) setHistory(items) })
      .catch((loadError) => { if (isCurrent) setError(loadError.message) })
      .finally(() => { if (isCurrent) setIsLoading(false) })
    return () => { isCurrent = false }
  }, [token, reloadCount])

  const summaryReady = !isLoading && !error
  const safeCount = summaryReady ? history.filter((item) => item.level === 'low').length : '—'
  const cautionCount = summaryReady ? history.filter((item) => item.level !== 'low').length : '—'
  const firstName = user?.name?.trim().split(/\s+/)[0] || 'there'
  const recent = history.slice(0, 3)

  return (
    <div className="dashboard-page">
      <section className="welcome-row"><div><span className="eyebrow">YOUR SAFETY, AT A GLANCE</span><h1>Good to see you, {firstName}<span className="wave">.</span></h1><p>A quick check can help you feel more confident about what lands in your inbox.</p></div><button className="button button-primary" type="button" onClick={() => onNavigate('scan')}>Check a message <span aria-hidden="true">→</span></button></section>
      <section className="hero-panel"><div className="hero-copy"><span className="hero-pill"><span /> YOUR SECOND PAIR OF EYES</span><h2>Not sure about that message?</h2><p>Paste it in and we’ll look for common scam warning signs together.</p><button className="button button-light" type="button" onClick={() => onNavigate('scan')}>Start a quick check <span aria-hidden="true">↗</span></button></div><div className="hero-art" aria-hidden="true"><div className="art-ring ring-back" /><div className="art-ring ring-front" /><div className="art-shield"><span>✓</span></div><div className="art-spark spark-a">✳</div><div className="art-spark spark-b">✦</div></div></section>
      <section className="summary-grid" aria-label="Your scan summary">
        <article className="summary-card"><span className="summary-icon icon-check">✓</span><div className="summary-label">Messages checked</div><strong>{summaryReady ? history.length : '—'}</strong><span className="summary-caption">in your account</span></article>
        <article className="summary-card"><span className="summary-icon icon-safe">⌁</span><div className="summary-label">Low risk</div><strong>{safeCount}</strong><span className="summary-caption">looked okay</span></article>
        <article className="summary-card"><span className="summary-icon icon-review">!</span><div className="summary-label">Worth a closer look</div><strong>{cautionCount}</strong><span className="summary-caption">use extra care</span></article>
      </section>
      <section className="dashboard-lower">
        <div className="recent-panel">
          <div className="section-heading"><div><span className="eyebrow">YOUR ACTIVITY</span><h2>Recent checks</h2></div><button type="button" className="text-button" onClick={() => onNavigate('history')}>See history <span aria-hidden="true">→</span></button></div>
          {isLoading ? <div className="empty-activity" role="status"><div><strong>Loading your recent checks…</strong></div></div>
            : error ? <div className="empty-activity" role="alert"><div><strong>Couldn’t load recent checks</strong><p>{error}</p></div><button className="text-button" type="button" onClick={() => setReloadCount((count) => count + 1)}>Try again</button></div>
              : recent.length ? <div className="recent-list">{recent.map((item) => <button type="button" className="recent-item" key={item.id} onClick={() => onNavigate('history')}><span className={`activity-dot dot-${item.level}`} /><span className="recent-message">{item.text}</span><span className="recent-result">{item.title}</span><span className="recent-arrow">↗</span></button>)}</div>
                : <div className="empty-activity"><span className="empty-icon">⌕</span><div><strong>Your checks will show up here</strong><p>Start with a message you’re unsure about.</p></div><button className="text-button" type="button" onClick={() => onNavigate('scan')}>Try a check →</button></div>}
        </div>
        <aside className="reminder-card"><span className="reminder-icon">✳</span><span className="eyebrow">A FRIENDLY REMINDER</span><h2>Pause before you click.</h2><p>Real companies won’t rush you into sharing a password or payment code.</p><button className="text-button" type="button" onClick={() => onNavigate('scan')}>Check something now <span aria-hidden="true">→</span></button></aside>
      </section>
      <p className="dashboard-disclaimer">ScamGuard checks for common warning signs. It can’t guarantee that a message is safe.</p>
    </div>
  )
}
