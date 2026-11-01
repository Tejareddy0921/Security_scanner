import { useEffect, useRef, useState } from 'react'
import DetectionResult from '../components/DetectionResult.jsx'
import ScamInput from '../components/ScamInput.jsx'
import { analyzeMessage } from '../services/scamService.js'
import '../style/pages/scam-input.css'

export default function ScamInputPage({ token }) {
  const [message, setMessage] = useState('')
  const [result, setResult] = useState(null)
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const activeRequestId = useRef(0)
  const activeController = useRef(null)

  useEffect(() => () => {
    activeRequestId.current += 1
    activeController.current?.abort()
  }, [])

  async function handleSubmit(event) {
    event.preventDefault()
    setError('')
    setResult(null)
    if (!message.trim()) {
      setError('Paste a message or link to check.')
      return
    }
    if (message.length > 5000) {
      setError('Keep the message under 5,000 characters.')
      return
    }

    const requestId = ++activeRequestId.current
    const submittedMessage = message
    const controller = new AbortController()
    activeController.current = controller
    setIsLoading(true)
    try {
      const nextResult = await analyzeMessage(submittedMessage, token, controller.signal)
      if (requestId === activeRequestId.current) setResult(nextResult)
    } catch (analysisError) {
      if (!controller.signal.aborted && requestId === activeRequestId.current) {
        setError(analysisError.message || 'The message could not be checked. Please try again.')
      }
    } finally {
      if (requestId === activeRequestId.current) setIsLoading(false)
      if (activeController.current === controller) activeController.current = null
    }
  }

  function handleMessageChange(value) {
    activeRequestId.current += 1
    activeController.current?.abort()
    activeController.current = null
    setMessage(value)
    setError('')
    setResult(null)
    setIsLoading(false)
  }

  return (
    <div className="scan-page">
      <header className="page-heading">
        <span className="eyebrow">MESSAGE CHECKER</span>
        <h1>Let’s take a closer look<span className="heading-dot">.</span></h1>
        <p>Paste a text, email, or link that doesn’t feel quite right.</p>
      </header>
      <div className="scan-layout">
        <section className="scan-panel">
          <div className="scan-panel-heading">
            <span className="scan-heading-icon" aria-hidden="true">⌕</span>
            <div><h2>What would you like to check?</h2><p>Submitted to your account for analysis.</p></div>
          </div>
          <ScamInput value={message} onChange={handleMessageChange} onSubmit={handleSubmit} isLoading={isLoading} />
          {error && <p className="scan-error" role="alert">{error}</p>}
          {isLoading && <p className="scan-status" role="status">Checking this message…</p>}
          <DetectionResult result={result} />
        </section>
        <aside className="scan-guide">
          <span className="guide-icon" aria-hidden="true">✳</span>
          <span className="eyebrow">LOOK OUT FOR</span>
          <h2>Little red flags can tell you a lot.</h2>
          <ul>
            <li><span>01</span>Pressure to act right away</li>
            <li><span>02</span>Requests for codes or passwords</li>
            <li><span>03</span>Unexpected payments or prizes</li>
            <li><span>04</span>Links from unfamiliar senders</li>
          </ul>
          <p>We look for common patterns, but always trust your judgment.</p>
        </aside>
      </div>
      <p className="scan-privacy">Your message is sent to theSecurity_scanner backend, analyzed, and saved to your account history.</p>
    </div>
  )
}
