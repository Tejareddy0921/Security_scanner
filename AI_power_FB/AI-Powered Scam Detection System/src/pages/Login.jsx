import { useState } from 'react'
import { useAuth } from '../hooks/useAuth.js'
import '../style/auth.css'
import '../style/pages/login.css'

export default function Login({ onNavigate }) {
  const { login } = useAuth()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  async function handleSubmit(event) {
    event.preventDefault()
    setError('')
    setIsSubmitting(true)
    try {
      await login(email, password)
      onNavigate('dashboard')
    } catch (loginError) {
      setError(loginError.message)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <main className="auth-page">
      <section className="auth-card">
        <a className="auth-brand" href="/login" onClick={(event) => { event.preventDefault(); onNavigate('login') }}><span className="brand-mark">S</span>Security_scanner<span className="brand-period">.</span></a>
        <span className="auth-kicker">A LITTLE MORE PEACE OF MIND</span>
        <h1>Welcome back</h1>
        <p className="auth-intro">Sign in to keep your digital life a little safer.</p>
        <form className="auth-form" onSubmit={handleSubmit}>
          <label htmlFor="login-email">Email address</label>
          <input id="login-email" type="email" autoComplete="email" value={email} onChange={(event) => setEmail(event.target.value)} placeholder="you@example.com" required />
          <label htmlFor="login-password">Password</label>
          <input id="login-password" type="password" autoComplete="current-password" value={password} onChange={(event) => setPassword(event.target.value)} placeholder="Enter your password" required />
          {error && <p className="form-error" role="alert">{error}</p>}
          <button className="button button-primary auth-submit" type="submit" disabled={isSubmitting}>{isSubmitting ? 'Signing in…' : 'Sign in'} <span aria-hidden="true">→</span></button>
        </form>
        <p className="auth-switch">New around here? <button type="button" onClick={() => onNavigate('register')}>Create an account</button></p>
        <p className="demo-note">Sign in with yourSecurity_scanner account.</p>
      </section>
      <aside className="auth-aside"><div className="auth-orbit orbit-one" /><div className="auth-orbit orbit-two" /><div className="auth-aside-content"><span className="auth-aside-icon">✳</span><span className="auth-aside-label">A calmer kind of internet</span><h2>Trust your instincts.<br />Check the details.</h2><p>ScamGuard helps you spot the red flags hiding in everyday messages.</p><div className="auth-aside-note"><span>“</span>When in doubt, take a moment to check.</div></div></aside>
    </main>
  )
}
