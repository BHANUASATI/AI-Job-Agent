import { useState, useEffect } from 'react'
import { useNavigate, Link } from 'react-router-dom'
import { useAuth } from '../authContext'
import { useToast } from '../components/Toast'
import './Login.css'  // shared auth page styles

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

/* ── Password strength helper ── */
function getStrength(pw) {
  if (!pw)          return { level: 0, label: '', cls: '' }
  let score = 0
  if (pw.length >= 8)             score++
  if (/[A-Z]/.test(pw))           score++
  if (/[0-9]/.test(pw))           score++
  if (/[^A-Za-z0-9]/.test(pw))   score++

  const map = [
    { label: 'Too weak',  cls: 'weak',   pct: 20  },
    { label: 'Fair',      cls: 'fair',   pct: 45  },
    { label: 'Good',      cls: 'good',   pct: 70  },
    { label: 'Strong',    cls: 'strong', pct: 100 },
  ]
  return { level: score, ...map[Math.min(score, 3)] }
}

export default function Signup() {
  const [name,    setName]    = useState('')
  const [email,   setEmail]   = useState('')
  const [pw,      setPw]      = useState('')
  const [pwConf,  setPwConf]  = useState('')
  const [errors,  setErrors]  = useState({})
  const [loading, setLoading] = useState(false)
  const [oauthConfig, setOauthConfig] = useState({ google_oauth_enabled: false, outlook_oauth_enabled: false })

  const { signup, login } = useAuth()
  const { success: toastSuccess } = useToast()
  const navigate = useNavigate()

  // Fetch which OAuth providers are configured on the backend
  useEffect(() => {
    fetch('/api/auth/config')
      .then((r) => r.json())
      .then((d) => setOauthConfig(d))
      .catch(() => {})
  }, [])

  const strength = getStrength(pw)

  const validate = () => {
    const e = {}
    if (!name.trim())           e.name    = 'Full name is required'
    if (!email.trim())          e.email   = 'Email is required'
    if (pw.length < 8)          e.pw      = 'Password must be at least 8 characters'
    if (pw !== pwConf)          e.pwConf  = 'Passwords do not match'
    return e
  }

  const handleSubmit = async (e) => {
    e.preventDefault()
    const errs = validate()
    if (Object.keys(errs).length) { setErrors(errs); return }

    setErrors({})
    setLoading(true)
    try {
      await signup(email, pw, name)
      await login(email, pw)
      toastSuccess('Account created!', `Welcome aboard, ${name.split(' ')[0]}.`)
      navigate('/dashboard')
    } catch (err) {
      setErrors({ server: err.response?.data?.detail || 'Signup failed. Please try again.' })
    } finally {
      setLoading(false)
    }
  }

  const handleGoogleSignup = async () => {
    try {
      const res  = await fetch('/api/auth/google')
      const data = await res.json()
      window.location.href = data.auth_url
    } catch {
      setErrors({ server: 'Could not connect to Google. Please try again.' })
    }
  }

  const handleOutlookSignup = async () => {
    try {
      const res  = await fetch('/api/auth/outlook')
      const data = await res.json()
      window.location.href = data.auth_url
    } catch {
      setErrors({ server: 'Could not connect to Outlook. Please try again.' })
    }
  }

  return (
    <div className="auth-page">
      {/* ── Hero (identical to login, hidden on mobile) ── */}
      <aside className="auth-hero" aria-hidden>
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
            Start your journey<br/>
            <span>in minutes</span>
          </h2>
          <p className="auth-hero__sub">
            Join thousands of professionals who automated their job search
            and landed better roles faster with AI.
          </p>

          <div className="auth-hero__features">
            {[
              { title: 'Free to start',       sub: 'No credit card required' },
              { title: 'Unlimited resumes',   sub: 'Upload and manage all versions' },
              { title: 'Gmail & Outlook',     sub: 'Connect your preferred email' },
            ].map((f) => (
              <div key={f.title} className="auth-hero__feature">
                <div className="auth-hero__feature-icon">
                  <svg viewBox="0 0 20 20" fill="currentColor" style={{width:18,height:18}}>
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd"/>
                  </svg>
                </div>
                <div className="auth-hero__feature-text">
                  <strong>{f.title}</strong>
                  <span>{f.sub}</span>
                </div>
              </div>
            ))}
          </div>
        </div>
      </aside>

      {/* ── Form panel ── */}
      <main className="auth-form-panel">
        <div className="auth-card">
          <div className="auth-card__header">
            <h1 className="auth-card__title">Create account</h1>
            <p className="auth-card__subtitle">Start automating your job search today</p>
          </div>

          {errors.server && (
            <div className="auth-alert auth-alert--error" role="alert">
              <svg viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M18 10a8 8 0 11-16 0 8 8 0 0116 0zm-7 4a1 1 0 11-2 0 1 1 0 012 0zm-1-9a1 1 0 00-1 1v4a1 1 0 102 0V6a1 1 0 00-1-1z" clipRule="evenodd"/>
              </svg>
              {errors.server}
            </div>
          )}

          <form className="auth-form" onSubmit={handleSubmit} noValidate>
            {/* Name */}
            <div className="form-field">
              <label className="form-field__label" htmlFor="signup-name">
                <svg viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M10 9a3 3 0 100-6 3 3 0 000 6zm-7 9a7 7 0 1114 0H3z" clipRule="evenodd"/>
                </svg>
                Full name
              </label>
              <input
                id="signup-name"
                type="text"
                autoComplete="name"
                className={`form-field__input${errors.name ? ' form-field__input--error' : ''}`}
                placeholder="Alex Johnson"
                value={name}
                onChange={(e) => setName(e.target.value)}
              />
              {errors.name && <span className="form-field__hint">{errors.name}</span>}
            </div>

            {/* Email */}
            <div className="form-field">
              <label className="form-field__label" htmlFor="signup-email">
                <svg viewBox="0 0 20 20" fill="currentColor">
                  <path d="M2.003 5.884L10 9.882l7.997-3.998A2 2 0 0016 4H4a2 2 0 00-1.997 1.884z"/>
                  <path d="M18 8.118l-8 4-8-4V14a2 2 0 002 2h12a2 2 0 002-2V8.118z"/>
                </svg>
                Email address
              </label>
              <input
                id="signup-email"
                type="email"
                autoComplete="email"
                className={`form-field__input${errors.email ? ' form-field__input--error' : ''}`}
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
              {errors.email && <span className="form-field__hint">{errors.email}</span>}
            </div>

            {/* Password */}
            <div className="form-field">
              <label className="form-field__label" htmlFor="signup-pw">
                <svg viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd"/>
                </svg>
                Password
              </label>
              <input
                id="signup-pw"
                type="password"
                autoComplete="new-password"
                className={`form-field__input${errors.pw ? ' form-field__input--error' : ''}`}
                placeholder="Min. 8 characters"
                value={pw}
                onChange={(e) => setPw(e.target.value)}
              />
              {pw && (
                <div className="password-strength">
                  <div className="password-strength__bar">
                    <div
                      className={`password-strength__fill password-strength__fill--${strength.cls}`}
                      style={{ width: `${strength.pct}%` }}
                    />
                  </div>
                  <span className={`password-strength__label password-strength__label--${strength.cls}`}>
                    {strength.label}
                  </span>
                </div>
              )}
              {errors.pw && <span className="form-field__hint">{errors.pw}</span>}
            </div>

            {/* Confirm password */}
            <div className="form-field">
              <label className="form-field__label" htmlFor="signup-pwconf">
                <svg viewBox="0 0 20 20" fill="currentColor">
                  <path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd"/>
                </svg>
                Confirm password
              </label>
              <input
                id="signup-pwconf"
                type="password"
                autoComplete="new-password"
                className={`form-field__input${errors.pwConf ? ' form-field__input--error' : ''}`}
                placeholder="Re-enter password"
                value={pwConf}
                onChange={(e) => setPwConf(e.target.value)}
              />
              {errors.pwConf && <span className="form-field__hint">{errors.pwConf}</span>}
            </div>

            <button type="submit" className="auth-btn" disabled={loading}>
              <span>
                {loading ? (
                  <><span className="btn-spinner" /> Creating account…</>
                ) : (
                  <>
                    <svg viewBox="0 0 20 20" fill="currentColor">
                      <path d="M8 9a3 3 0 100-6 3 3 0 000 6zM8 11a6 6 0 016 6H2a6 6 0 016-6zM16 7a1 1 0 10-2 0v1h-1a1 1 0 100 2h1v1a1 1 0 102 0v-1h1a1 1 0 100-2h-1V7z"/>
                    </svg>
                    Create Account
                  </>
                )}
              </span>
            </button>
          </form>

          <div className="auth-divider">or sign up with</div>

          {(oauthConfig.google_oauth_enabled || oauthConfig.outlook_oauth_enabled) ? (
            <div className="oauth-grid">
              {oauthConfig.google_oauth_enabled && (
                <button type="button" className="oauth-btn" onClick={handleGoogleSignup}>
                  <GoogleIcon /> Google
                </button>
              )}
              {oauthConfig.outlook_oauth_enabled && (
                <button type="button" className="oauth-btn" onClick={handleOutlookSignup}>
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

          <p className="auth-terms">
            By creating an account you agree to our{' '}
            <a href="#">Terms of Service</a> and <a href="#">Privacy Policy</a>.
          </p>

          <p className="auth-footer">
            Already have an account?{' '}
            <Link to="/login">Sign in</Link>
          </p>
        </div>
      </main>
    </div>
  )
}
