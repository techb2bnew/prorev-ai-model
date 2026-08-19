import { useState } from 'react'
import { ErrorAlert, Spinner } from '../components/common.jsx'
import { useAuth } from '../context/AuthContext.jsx'

export default function LoginPage() {
  const { signIn, signUp } = useAuth()
  const [mode, setMode] = useState('login')
  const [fields, setFields] = useState({ email: '', password: '', full_name: '', phone: '' })
  const [error, setError] = useState(null)
  const [busy, setBusy] = useState(false)

  const isRegister = mode === 'register'

  function update(key) {
    return (event) => setFields((current) => ({ ...current, [key]: event.target.value }))
  }

  async function submit(event) {
    event.preventDefault()
    setError(null)
    setBusy(true)
    try {
      if (isRegister) {
        await signUp({
          email: fields.email,
          password: fields.password,
          full_name: fields.full_name || null,
          phone: fields.phone || null,
        })
      } else {
        await signIn(fields.email, fields.password)
      }
    } catch (caught) {
      setError(caught)
    } finally {
      setBusy(false)
    }
  }

  return (
    <div className="auth-shell">
      <div className="auth-card">
        <div className="auth-head">
          <div className="brand" style={{ justifyContent: 'center', marginBottom: 10 }}>
            <div className="brand-mark">D</div>
            <div style={{ textAlign: 'left' }}>
              <div className="brand-name">Dent Detection</div>
              <div className="brand-sub">Vehicle damage inspection</div>
            </div>
          </div>
          <p className="muted small">
            {isRegister ? 'Create an account to run inspections.' : 'Sign in to run inspections.'}
          </p>
        </div>

        <form className="card" onSubmit={submit}>
          <ErrorAlert error={error} />

          <div className="field">
            <label htmlFor="email">Email</label>
            <input
              id="email"
              type="email"
              required
              autoComplete="email"
              value={fields.email}
              onChange={update('email')}
              placeholder="you@example.com"
            />
          </div>

          <div className="field">
            <label htmlFor="password">Password</label>
            <input
              id="password"
              type="password"
              required
              autoComplete={isRegister ? 'new-password' : 'current-password'}
              value={fields.password}
              onChange={update('password')}
              placeholder={isRegister ? 'min 8 chars, letters and numbers' : '••••••••'}
            />
          </div>

          {isRegister && (
            <>
              <div className="field">
                <label htmlFor="full_name">Full name <span className="muted">(optional)</span></label>
                <input id="full_name" value={fields.full_name} onChange={update('full_name')} />
              </div>
              <div className="field">
                <label htmlFor="phone">Phone <span className="muted">(optional)</span></label>
                <input id="phone" value={fields.phone} onChange={update('phone')} />
              </div>
            </>
          )}

          <button className="btn-primary btn-lg" type="submit" disabled={busy} style={{ width: '100%' }}>
            {busy ? <Spinner /> : isRegister ? 'Create account' : 'Sign in'}
          </button>

          <div className="auth-toggle">
            {isRegister ? 'Already have an account?' : 'No account yet?'}
            <button
              type="button"
              onClick={() => {
                setMode(isRegister ? 'login' : 'register')
                setError(null)
              }}
            >
              {isRegister ? 'Sign in' : 'Register'}
            </button>
          </div>
        </form>

        <p className="muted small" style={{ textAlign: 'center', marginTop: 12 }}>
          Calls <span className="mono">POST /api/v1/auth/{isRegister ? 'register' : 'login'}</span>
        </p>
      </div>
    </div>
  )
}
