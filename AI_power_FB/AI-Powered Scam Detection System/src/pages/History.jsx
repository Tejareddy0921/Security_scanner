import { useEffect, useState } from 'react'
import { getScanHistory } from '../services/scamService.js'
import '../style/pages/history.css'

function formatDate(value) {
  const date = new Date(value)
  return Number.isNaN(date.getTime()) ? 'Unknown date' : date.toLocaleString(undefined, { dateStyle: 'medium', timeStyle: 'short' })
}

export default function History({ token }) {
  const [history, setHistory] = useState([])
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(true)
  const [reloadCount, setReloadCount] = useState(0)

  useEffect(() => {
    let isCurrent = true
    setIsLoading(true)
    setError('')
    getScanHistory(token)
      .then((items) => { if (isCurrent) setHistory(items) })
      .catch((loadError) => { if (isCurrent) setError(loadError.message) })
      .finally(() => { if (isCurrent) setIsLoading(false) })
    return () => { isCurrent = false }
  }, [token, reloadCount])

  return (
    <div className="history-page">
      <header className="page-heading">
        <span className="eyebrow">YOUR ACTIVITY</span>
        <h1>Scan history<span className="heading-dot">.</span></h1>
        <p>Messages you’ve checked with yourSecurity_scanner account.</p>
      </header>
      <section className="history-panel">
        {isLoading ? <div className="history-empty" role="status"><h2>Loading your checks…</h2></div> : error ? <div className="history-empty" role="alert">
          <h2>Couldn’t load your checks</h2>
          <p>{error}</p>
          <button className="button button-primary history-retry" type="button" onClick={() => setReloadCount((count) => count + 1)}>Try again</button>
        </div> : history.length ? <>
          <div className="history-summary"><span>{history.length} {history.length === 1 ? 'check' : 'checks'}</span><span>Saved to your account</span></div>
          <div className="history-list">{history.map((item) => <article className="history-item" key={item.id}>
            <div className={`history-status status-${item.level}`}><span aria-hidden="true">{item.level === 'high' ? '!' : item.level === 'medium' ? '?' : '✓'}</span></div>
            <div className="history-main">
              <div className="history-meta"><strong>{item.title}</strong><time dateTime={item.checkedAt}>{formatDate(item.checkedAt)}</time></div>
              <p>{item.text}</p>
              <span className="history-guidance">{item.guidance}</span>
            </div>
            <div className="history-score"><strong>{item.score === null ? '—' : `${item.score}%`}</strong><span>assessment</span></div>
          </article>)}</div>
        </> : <div className="history-empty"><span className="empty-icon">◷</span><h2>No checks yet</h2><p>Messages you check will be saved to your account here.</p></div>}
      </section>
      <p className="history-footnote">Your scan history is linked to yourSecurity_scanner account.</p>
    </div>
  )
}
