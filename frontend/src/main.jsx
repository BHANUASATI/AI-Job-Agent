import { createRoot } from 'react-dom/client'
import { BrowserRouter } from 'react-router-dom'
import './index.css'
import App from './App.jsx'
import { AuthProvider } from './authContext.jsx'

/**
 * Pre-save OAuth token BEFORE React renders.
 *
 * After Google/Microsoft OAuth, the backend redirects to:
 *   http://localhost:5173/auth/callback?token=<jwt>&provider=google
 *
 * React boots fresh on that page load — AuthProvider reads localStorage
 * in its useState initialiser. If we save the token here (synchronously,
 * before anything renders), AuthProvider picks it up on the very first
 * render and fires /api/auth/me with a valid Bearer token.
 */
;(function preSaveOAuthToken() {
  try {
    const params = new URLSearchParams(window.location.search)
    const token  = params.get('token')

    if (token && window.location.pathname === '/auth/callback') {
      localStorage.setItem('token', token)
      // Clean the token out of the URL so it isn't bookmarked / logged
      const provider = params.get('provider') || ''
      const clean = provider
        ? `${window.location.pathname}?provider=${provider}`
        : window.location.pathname
      window.history.replaceState({}, '', clean)
    }
  } catch {
    // Never crash here — worst case OAuthCallback handles it
  }
})()

createRoot(document.getElementById('root')).render(
  <BrowserRouter>
    <AuthProvider>
      <App />
    </AuthProvider>
  </BrowserRouter>,
)
