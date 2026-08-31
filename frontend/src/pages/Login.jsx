import { useState, useEffect, useRef } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../authContext'
import { useToast } from '../components/Toast'
import './Login.css'

/* ── Floating particles on the hero panel ── */
function Particles() {
  const particles = useRef(
    Array.from({ length: 18 }, (_, i) => ({
      id: i,
      size:  6  + Math.random() * 10,
      left:  Math.random() * 100,
      delay: Math.random() * 8,
      dur:   8  + Math.random() * 10,
    }))
  )

  return (
    <div className="auth-hero__particles" aria-hidden>
      {particles.current.map((p) => (
        <span
          key={p.id}
          className="auth-hero__particle"
          style={{
            width:  p.size,
            height: p.size,
            left:   `${p.left}%`,
            bottom: '-5%',
            animationDelay:    `${p.delay}s`,
            animationDuration: `${p.dur}s`,
          }}
        />
      ))}
    </div>
  )
}

/* ── Google G logo SVG ── */
function GoogleIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden>
      <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
      <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
      <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
      <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
    </svg>
  )
}

/* ── Microsoft icon ── */
function MicrosoftIcon() {
  return (
    <svg viewBox="0 0 24 24" aria-hidden>
      <rect x="1"  y="1"  width="10" height="10" fill="#F25022"/>
      <rect x="13" y="1"  width="10" height="10" fill="#7FBA00"/>
      <rect x="1"  y="13" width="10" height="10" fill="#00A4EF"/>
      <rect x="13" y="13" width="10" height="10" fill="#FFB900"/>
    </svg>
  )
}

export default function Login() {
  const [email,    setEmail]    = useState('')
  const [password, setPassword] = useState('')
  const [error,    setError]    = useState('')
  const [loading,  setLoading]  = useState(false)
  const [oauthConfig, setOauthConfig] = useState({ google_oauth_enabled: false, outlook_oauth_enabled: false })
  const { login } = useAuth()
  const { success: toastSuccess } = useToast()
  const navigate = useNavigate()

  // Fetch which OAuth providers are actually configured on the backend
  useEffect(() => {
    fetch('/api/auth/config')
      .then((r) => r.json())
      .then((d) => setOauthConfig(d))
      .catch(() => {}) // silently ignore — buttons stay hidden
  }, [])

  const handleSubmit = async (e) => {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      const data = await login(email, password)
      toastSuccess('Welcome back!', `Good to see you, ${data.user?.name || 'there'}.`)
      navigate('/dashboard')
    } catch (err) {
      setError(err.response?.data?.detail || 'Invalid email or password. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleGoogleLogin = async () => {
    try {
      const res  = await fetch('/api/auth/google')
      const data = await res.json()
      window.location.href = data.auth_url
    } catch {
      setError('Could not connect to Google. Please try again.')
    }
  }

  const handleOutlookLogin = async () => {
    try {
      const res  = await fetch('/api/auth/outlook')
      const data = await res.json()
      window.location.href = data.auth_url
    } catch {
      setError('Could not connect to Outlook. Please try again.')
    }
  }

  return (
    <div className="auth-page">
      {/* ── Left decorative hero ── */}
      <aside className="auth-hero" aria-hidden>
        <Particles />
        <div className="auth-hero__content">
          <div className="auth-hero__logo">
            <div className="auth-hero__logo-icon">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
                <path d="M12 2L2 7l10 5 10-5-10-5z"/>
                <path d="M2 17l10 5 10-5"/>
                <path d="M2 12l10 5 10-5"/>
              </svg>
            </div>
            <span className="auth-hero__logo-text">AI Job Agent</span>
          </div>

          <h2 className="auth-hero__tagline">
            Land your dream job<br/>
            <span>powered by AI</span>
          </h2>
          <p className="auth-hero__sub">
            Automate your entire job application workflow — from resume matching
            to personalised email generation in seconds.
          </p>

          <div className="auth-hero__features">
            {[
              {
                icon: (
                  <svg viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M6.267 3.455a3.066 3.066 0 001.745-.723 3.066 3.066 0 013.976 0 3.066 3.066 0 001.745.723 3.066 3.066 0 012.812 2.812c.051.643.304 1.254.723 1.745a3.066 3.066 0 010 3.976 3.066 3.066 0 00-.723 1.745 3.066 3.066 0 01-2.812 2.812 3.066 3.066 0 00-1.745.723 3.066 3.066 0 01-3.976 0 3.066 3.066 0 00-1.745-.723 3.066 3.066 0 01-2.812-2.812 3.066 3.066 0 00-.723-1.745 3.066 3.066 0 010-3.976 3.066 3.066 0 00.723-1.745 3.066 3.066 0 012.812-2.812zm7.44 5.252a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd"/>
                  </svg>
                ),
                title: 'Smart Resume Matching',
                sub:   'AI picks the best resume for every job',
              },
              {
                icon: (
                  <svg viewBox="0 0 20 20" fill="currentColor">
                    <path d="M2.003 5.884L10 9.882l7.997-3.998A2 2 0 0016 4H4a2 2 0 00-1.997 1.884z"/>
                    <path d="M18 8.118l-8 4-8-4V14a2 2 0 002 2h12a2 2 0 002-2V8.118z"/>
                  </svg>
                ),
                title: 'Auto Email Generation',
                sub:   'Personalised cover emails in one click',
              },
              {
                icon: (
                  <svg viewBox="0 0 20 20" fill="currentColor">
                    <path fillRule="evenodd" d="M3 3a1 1 0 000 2v8a2 2 0 002 2h2.586l-1.293 1.293a1 1 0 101.414 1.414L10 15.414l2.293 2.293a1 1 0 001.414-1.414L12.414 15H15a2 2 0 002-2V5a1 1 0 100-2H3zm11.707 4.707a1 1 0 00-1.414-1.414L10 9.586 8.707 8.293a1 1 0 00-1.414 0l-2 2a1 1 0 101.414 1.414L8 10.414l1.293 1.293a1 1 0 001.414 0l4-4z" clipRule="evenodd"/>
                  </svg>
                ),
                title: 'Real-time Analytics',
                sub:   'Track all your applications in one place',
              },
            ].map((f) => (
              <div key={f.title} className="auth-hero__feature">
                <div className="auth-hero__feature-icon">{f.icon}</div>
                <div className="auth-hero__feature-text">
                  <strong>{f.title}</strong>
                  <span>{f.sub}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </aside>

      {/* ── Right form panel ── */}
      <main className="auth-form-panel">
        <div className="auth-card">
          <div className="auth-card__header">
            <h1 className="auth-card__title">Welcome back</h1>
            <p className="auth-card__subtitle">Sign in to continue to your dashboard</p>
          </div>

          {error && (
            <div className="auth-alert auth-alert--error" role="alert">
              <svg viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd"/>
              </svg>
              {error}
            </div>
          )}

          <form className="auth-form" onSubmit={handleSubmit} noValidate>
            <div className="form-field">
              <label className="form-field__label" htmlFor="login-email">
                <svg viewBox="0 0 20 20" fill="currentColor">
                  <path d="M2.003 5.884L10 9.882l7.997-3.998A2 2 0 0016 4H4a2 2 0 00-1.997 1.884z"/>
                  <path d="M18 8.118l-8 4-8-4V14a2 2 0 002 2h12a2 2 0 002-2V8.118z"/>
                </svg>
                Email address
              </label>
              <div className="form-field__input-wrapper">
                <input
                  id="login-email"
                  type="email"
                  autoComplete="email"
                  className="form-field__input"
                  placeholder="you@example.com"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>
            </div>

            <div className="form-field">
              <label className="form-field__label" htmlFor="login-password">
                <svg viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd"/>
                </svg>
                Password
              </label>
              <div className="form-field__input-wrapper">
                <input
                  id="login-password"
                  type="password"
                  autoComplete="current-password"
                  className="form-field__input"
                  placeholder="••••••••"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                />
              </div>
            </div>

            <button type="submit" className="auth-btn" disabled={loading}>
              <span>
                {loading ? (
                  <><span className="btn-spinner" /> Signing in…</>
                ) : (
                  <>
                    <svg viewBox="0 0 20 20" fill="currentColor">
                      <path fillRule="evenodd" d="M3 3a1 1 0 011 1v12a1 1 0 11-2 0V4a1 1 0 011-1zm7.707 3.293a1 1 0 010 1.414L9.414 9H17a1 1 0 110 2H9.414l1.293 1.293a1 1 0 01-1.414 1.414l-3-3a1 1 0 010-1.414l3-3a1 1 0 011.414 0z" clipRule="evenodd"/>
                    </svg>
                    Sign In
                  </>
                )}
              </span>
            </button>
          </form>

          <div className="auth-divider">or continue with</div>

          {(oauthConfig.google_oauth_enabled || oauthConfig.outlook_oauth_enabled) ? (
            <div className="oauth-grid">
              {oauthConfig.google_oauth_enabled && (
                <button type="button" className="oauth-btn" onClick={handleGoogleLogin}>
                  <GoogleIcon /> Google
                </button>
              )}
              {oauthConfig.outlook_oauth_enabled && (
                <button type="button" className="oauth-btn" onClick={handleOutlookLogin}>
                  <MicrosoftIcon /> Outlook
                </button>
              )}
            </div>
          ) : (
            <div style={{
              textAlign: 'center',
              fontSize: '0.8125rem',
              color: '#94a3b8',
              padding: '0.75rem 1rem',
              background: '#f8fafc',
              borderRadius: '10px',
              border: '1px dashed #e2e8f0',
              marginBottom: '1.5rem',
            }}>
              OAuth providers not configured.{' '}
              <span style={{ color: '#6366f1' }}>Use email & password above.</span>
            </div>
          )}

          <p className="auth-footer">
            Don&apos;t have an account?{' '}
            <Link to="/signup">Create one free</Link>
          </p>
        </div>
      </main>
    </div>
  )
}
