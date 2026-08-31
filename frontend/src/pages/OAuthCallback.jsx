/**
 * OAuthCallback.jsx
 *
 * Backend redirects here after Google / Microsoft OAuth:
 *   http://localhost:5173/auth/callback?token=<jwt>&provider=google
 *   http://localhost:5173/auth/callback?error=<msg>
 *
 * main.jsx (IIFE, before React boots) already saved ?token to localStorage
 * and stripped it from the URL.
 *
 * This component just calls /auth/me to hydrate React state, then
 * navigates to /dashboard.  It handles its own error UI — it does NOT
 * call logout() so a transient /auth/me failure can't wipe the token.
 */
import { useEffect, useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router-dom'
import { useAuth } from '../authContext'

export default function OAuthCallback() {
  const [searchParams]        = useSearchParams()
  const [status,   setStatus] = useState('loading')
  const [message, setMessage] = useState('')
  const { refreshUser }       = useAuth()
  const navigate              = useNavigate()

  useEffect(() => {
    const error = searchParams.get('error')
    if (error) {
      setMessage(decodeURIComponent(error))
      setStatus('error')
      return
    }

    const token = localStorage.getItem('token')
    if (!token) {
      setMessage('No token was received from Google. Please try signing in again.')
      setStatus('error')
      return
    }

    // refreshUser now throws on failure instead of calling logout()
    // so a failed /auth/me here won't wipe the token
    refreshUser()
      .then(() => navigate('/dashboard', { replace: true }))
      .catch((err) => {
        const detail = err.response?.data?.detail || err.message || 'Authentication failed'
        console.error('OAuthCallback refreshUser failed:', detail)
        setMessage(`Sign-in failed: ${detail}. Please try again.`)
        setStatus('error')
      })
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  const wrap = {
    minHeight: '100vh', display: 'flex', alignItems: 'center',
    justifyContent: 'center',
    background: 'linear-gradient(135deg,#0f172a 0%,#1e1b4b 50%,#0f172a 100%)',
    padding: '2rem', fontFamily: "'Inter', system-ui, sans-serif",
  }
  const card = {
    background: 'white', borderRadius: '16px', padding: '2.5rem 2rem',
    maxWidth: '420px', width: '100%', textAlign: 'center',
    boxShadow: '0 25px 50px rgba(0,0,0,0.35)',
  }

  if (status === 'loading') {
    return (
      <div style={wrap}>
        <div style={card}>
          <style>{`@keyframes _sp{to{transform:rotate(360deg)}}`}</style>
          <div style={{
            width:52, height:52, borderRadius:'50%',
            border:'4px solid #e0e7ff', borderTopColor:'#6366f1',
            animation:'_sp 0.8s linear infinite', margin:'0 auto 1.25rem',
          }}/>
          <h2 style={{fontSize:'1.25rem',fontWeight:700,color:'#0f172a',marginBottom:'.5rem'}}>
            Signing you in…
          </h2>
          <p style={{fontSize:'.9rem',color:'#64748b'}}>Setting up your account.</p>
        </div>
      </div>
    )
  }

  return (
    <div style={wrap}>
      <div style={card}>
        <div style={{
          width:52,height:52,background:'#fee2e2',borderRadius:'50%',
          display:'flex',alignItems:'center',justifyContent:'center',
          margin:'0 auto 1.25rem',color:'#ef4444',
        }}>
          <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
            <circle cx="12" cy="12" r="10"/>
            <line x1="15" y1="9" x2="9" y2="15"/>
            <line x1="9" y1="9" x2="15" y2="15"/>
          </svg>
        </div>
        <h2 style={{fontSize:'1.25rem',fontWeight:700,color:'#0f172a',marginBottom:'.5rem'}}>
          Sign-in failed
        </h2>
        <p style={{fontSize:'.875rem',color:'#64748b',marginBottom:'1.5rem',lineHeight:1.6}}>
          {message}
        </p>
        <button
          onClick={() => navigate('/login', { replace: true })}
          style={{
            padding:'.75rem 1.5rem',
            background:'linear-gradient(135deg,#6366f1,#8b5cf6)',
            color:'white',border:'none',borderRadius:'10px',
            fontWeight:600,fontSize:'.9375rem',cursor:'pointer',
          }}
        >
          Back to login
        </button>
      </div>
    </div>
  )
}
