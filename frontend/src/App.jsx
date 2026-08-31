import { Routes, Route, Navigate, useLocation } from 'react-router-dom'
import { Component } from 'react'
import { useAuth } from './authContext'
import { ToastProvider } from './components/Toast'
import Login from './pages/Login'
import Signup from './pages/Signup'
import Dashboard from './pages/Dashboard'
import OAuthCallback from './pages/OAuthCallback'
import './App.css'

/* ── Error boundary — catches JS crashes and shows them instead of white screen ── */
class ErrorBoundary extends Component {
  constructor(props) { super(props); this.state = { error: null } }
  static getDerivedStateFromError(error) { return { error } }
  render() {
    if (this.state.error) {
      return (
        <div style={{
          minHeight:'100vh', display:'flex', flexDirection:'column',
          alignItems:'center', justifyContent:'center',
          background:'#f8fafc', padding:'2rem', fontFamily:'system-ui,sans-serif'
        }}>
          <div style={{
            background:'white', borderRadius:16, padding:'2rem', maxWidth:560,
            width:'100%', boxShadow:'0 4px 24px rgba(0,0,0,0.1)',
            border:'1px solid #fee2e2'
          }}>
            <h2 style={{color:'#dc2626', marginBottom:'0.75rem', fontSize:'1.25rem'}}>
              Something went wrong
            </h2>
            <pre style={{
              background:'#f8fafc', padding:'1rem', borderRadius:8,
              fontSize:'0.8125rem', color:'#475569', overflowX:'auto',
              whiteSpace:'pre-wrap', wordBreak:'break-word'
            }}>
              {this.state.error.message}
            </pre>
            <button
              onClick={() => { this.setState({error:null}); window.location.href='/login' }}
              style={{
                marginTop:'1rem', padding:'0.625rem 1.25rem',
                background:'#6366f1', color:'white', border:'none',
                borderRadius:8, cursor:'pointer', fontWeight:600
              }}
            >
              Back to login
            </button>
          </div>
        </div>
      )
    }
    return this.props.children
  }
}

/* ── Animated loading screen shown while JWT is validated ── */
function AppLoader() {
  return (
    <div className="app-loading">
      <div className="app-loading__logo">
        <div className="app-loading__logo-icon">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
            <path d="M12 2L2 7l10 5 10-5-10-5z" />
            <path d="M2 17l10 5 10-5" />
            <path d="M2 12l10 5 10-5" />
          </svg>
        </div>
        <span className="app-loading__logo-text">
          AI Job <span>Agent</span>
        </span>
      </div>
      <div className="app-loading__spinner">
        <span className="app-loading__dot" />
        <span className="app-loading__dot" />
        <span className="app-loading__dot" />
      </div>
    </div>
  )
}

/* ── Wrap each page in a fade-in transition ── */
function AnimatedPage({ children }) {
  const location = useLocation()
  return (
    <div className="page-enter" key={location.pathname}>
      {children}
    </div>
  )
}

/* ── Protected route helper ── */
function ProtectedRoute({ children }) {
  const { user } = useAuth()
  return user ? children : <Navigate to="/login" replace />
}

/* ── Public route helper (redirect authenticated users away) ── */
function PublicRoute({ children }) {
  const { user } = useAuth()
  return !user ? children : <Navigate to="/dashboard" replace />
}

function App() {
  const { loading } = useAuth()

  if (loading) return <AppLoader />

  return (
    <ErrorBoundary>
      <ToastProvider>
        <Routes>
          <Route path="/login" element={<PublicRoute><AnimatedPage><Login /></AnimatedPage></PublicRoute>} />
          <Route path="/signup" element={<PublicRoute><AnimatedPage><Signup /></AnimatedPage></PublicRoute>} />
          <Route path="/dashboard" element={<ProtectedRoute><AnimatedPage><Dashboard /></AnimatedPage></ProtectedRoute>} />
          <Route path="/auth/callback" element={<OAuthCallback />} />
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </ToastProvider>
    </ErrorBoundary>
  )
}

export default App
