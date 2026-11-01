import { useState } from 'react'
import { useAuth } from '../hooks/useAuth.js'
import '../style/auth.css'
import '../style/pages/register.css'

export default function Register({ onNavigate }) {
  const { register } = useAuth()
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')
  const [isSubmitting, setIsSubmitting] = useState(false)

  async function handleSubmit(event) {
    event.preventDefault()
    setError('')
    setIsSubmitting(true)
    try {
      await register(name, email, password)
      onNavigate('dashboard')
    } catch (registerError) {
      setError(registerError.message)
    } finally {
      setIsSubmitting(false)
    }
  }

  return (
    <main className="auth-page register-page">
      <section className="auth-card">
        <a className="auth-brand" href="/login" onClick={(event) => { event.preventDefault(); onNavigate('login') }}><span className="brand-mark">S</span>Security_scanner<span className="brand-period">.</span></a>
        <span className="auth-kicker">MAKE SAFER YOUR NEW HABIT</span>
        <h1>Start with a little care</h1>
        <p className="auth-intro">Create your free account. It only takes a moment.</p>
        <form className="auth-form" onSubmit={handleSubmit}>
          <label htmlFor="register-name">Your name</label>
          <input id="register-name" type="text" autoComplete="name" value={name} onChange={(event) => setName(event.target.value)} placeholder="Jamie Taylor" minLength={2} required />
          <label htmlFor="register-email">Email address</label>
          <input id="register-email" type="email" autoComplete="email" value={email} onChange={(event) => setEmail(event.target.value)} placeholder="you@example.com" required />
          <label htmlFor="register-password">Create a password</label>
          <input id="register-password" type="password" autoComplete="new-password" value={password} onChange={(event) => setPassword(event.target.value)} placeholder="At least 8 characters" minLength={8} required />
          {error && <p className="form-error" role="alert">{error}</p>}
          <button className="button button-primary auth-submit" type="submit" disabled={isSubmitting}>{isSubmitting ? 'Creating account…' : 'Create my account'} <span aria-hidden="true">→</span></button>
        </form>
        <p className="auth-switch">Already have an account? <button type="button" onClick={() => onNavigate('login')}>Sign in</button></p>
        <p className="demo-note">Your profile and checks will be linked to your account.</p>
      </section>
      <aside className="auth-aside"><div className="auth-orbit orbit-one" /><div className="auth-orbit orbit-two" /><div className="auth-aside-content"><span className="auth-aside-icon">✳</span><span className="auth-aside-label">A calmer kind of internet</span><h2>Small checks.<br />Stronger confidence.</h2><p>Get a second look at suspicious messages before you decide what to do.</p><div className="auth-aside-note"><span>“</span>Your safety starts with a pause.</div></div></aside>
    </main>
  )
}
