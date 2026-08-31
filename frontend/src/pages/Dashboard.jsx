import { useState, useEffect, useRef, useCallback } from 'react'
import { useNavigate } from 'react-router-dom'
import { useAuth, api } from '../authContext'
import { useToast } from '../components/Toast'
import './Dashboard.css'

/* ──────────────────────────────────────────────
   SVG icon helpers — inline, no extra dep
────────────────────────────────────────────── */
const Icon = {
  Layers: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M12 2L2 7l10 5 10-5-10-5z"/><path d="M2 17l10 5 10-5"/><path d="M2 12l10 5 10-5"/>
    </svg>
  ),
  Dashboard: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/>
      <rect x="14" y="14" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/>
    </svg>
  ),
  FileText: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M14 2H6a2 2 0 00-2 2v16a2 2 0 002 2h12a2 2 0 002-2V8z"/>
      <polyline points="14 2 14 8 20 8"/><line x1="16" y1="13" x2="8" y2="13"/>
      <line x1="16" y1="17" x2="8" y2="17"/><polyline points="10 9 9 9 8 9"/>
    </svg>
  ),
  Zap: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <polygon points="13 2 3 14 12 14 11 22 21 10 12 10 13 2"/>
    </svg>
  ),
  Mail: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M4 4h16c1.1 0 2 .9 2 2v12c0 1.1-.9 2-2 2H4c-1.1 0-2-.9-2-2V6c0-1.1.9-2 2-2z"/>
      <polyline points="22,6 12,13 2,6"/>
    </svg>
  ),
  TrendingUp: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <polyline points="23 6 13.5 15.5 8.5 10.5 1 18"/>
      <polyline points="17 6 23 6 23 12"/>
    </svg>
  ),
  CheckCircle: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M22 11.08V12a10 10 0 11-5.93-9.14"/>
      <polyline points="22 4 12 14.01 9 11.01"/>
    </svg>
  ),
  Clock: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <circle cx="12" cy="12" r="10"/>
      <polyline points="12 6 12 12 16 14"/>
    </svg>
  ),
  XCircle: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <circle cx="12" cy="12" r="10"/>
      <line x1="15" y1="9" x2="9" y2="15"/><line x1="9" y1="9" x2="15" y2="15"/>
    </svg>
  ),
  Upload: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <polyline points="16 16 12 12 8 16"/>
      <line x1="12" y1="12" x2="12" y2="21"/>
      <path d="M20.39 18.39A5 5 0 0018 9h-1.26A8 8 0 103 16.3"/>
    </svg>
  ),
  Trash: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <polyline points="3 6 5 6 21 6"/><path d="M19 6l-1 14a2 2 0 01-2 2H8a2 2 0 01-2-2L5 6"/>
      <path d="M10 11v6"/><path d="M14 11v6"/>
      <path d="M9 6V4a1 1 0 011-1h4a1 1 0 011 1v2"/>
    </svg>
  ),
  Logout: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M9 21H5a2 2 0 01-2-2V5a2 2 0 012-2h4"/>
      <polyline points="16 17 21 12 16 7"/>
      <line x1="21" y1="12" x2="9" y2="12"/>
    </svg>
  ),
  Link: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <path d="M10 13a5 5 0 007.54.54l3-3a5 5 0 00-7.07-7.07l-1.72 1.71"/>
      <path d="M14 11a5 5 0 00-7.54-.54l-3 3a5 5 0 007.07 7.07l1.71-1.71"/>
    </svg>
  ),
  Menu: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <line x1="3" y1="12" x2="21" y2="12"/>
      <line x1="3" y1="6"  x2="21" y2="6"/>
      <line x1="3" y1="18" x2="21" y2="18"/>
    </svg>
  ),
  X: () => (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
      <line x1="18" y1="6" x2="6" y2="18"/>
      <line x1="6"  y1="6" x2="18" y2="18"/>
    </svg>
  ),
  Google: () => (
    <svg viewBox="0 0 24 24">
      <path d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z" fill="#4285F4"/>
      <path d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z" fill="#34A853"/>
      <path d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z" fill="#FBBC05"/>
      <path d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z" fill="#EA4335"/>
    </svg>
  ),
  Microsoft: () => (
    <svg viewBox="0 0 24 24">
      <rect x="1"  y="1"  width="10" height="10" fill="#F25022"/>
      <rect x="13" y="1"  width="10" height="10" fill="#7FBA00"/>
      <rect x="1"  y="13" width="10" height="10" fill="#00A4EF"/>
      <rect x="13" y="13" width="10" height="10" fill="#FFB900"/>
    </svg>
  ),
}

/* ──────────────────────────────────────────────
   Status pill component
────────────────────────────────────────────── */
function StatusPill({ status }) {
  const map = {
    sent:    { cls: 'sent',    label: 'Sent',    icon: <Icon.CheckCircle /> },
    pending: { cls: 'pending', label: 'Pending', icon: <Icon.Clock /> },
    failed:  { cls: 'failed',  label: 'Failed',  icon: <Icon.XCircle /> },
    draft:   { cls: 'draft',   label: 'Draft',   icon: <Icon.FileText /> },
  }
  const s = map[status?.toLowerCase()] ?? map.draft
  return (
    <span className={`status-pill status-pill--${s.cls}`}>
      {s.icon} {s.label}
    </span>
  )
}

/* ──────────────────────────────────────────────
   Score badge
────────────────────────────────────────────── */
function ScoreBadge({ score }) {
  const pct = Math.round((score ?? 0) * 100)
  const cls = pct >= 75 ? 'high' : pct >= 45 ? 'medium' : 'low'
  return <span className={`score-badge score-badge--${cls}`}>{pct}%</span>
}

/* ──────────────────────────────────────────────
   Toggle switch
────────────────────────────────────────────── */
function Toggle({ checked, onChange, id }) {
  return (
    <label className="toggle-switch" htmlFor={id}>
      <input id={id} type="checkbox" checked={checked} onChange={onChange} />
      <span className="toggle-switch__track" />
      <span className="toggle-switch__thumb" />
    </label>
  )
}

/* ──────────────────────────────────────────────
   MAIN DASHBOARD
────────────────────────────────────────────── */
const TABS = [
  { id: 'overview',  label: 'Overview',     icon: <Icon.Dashboard /> },
  { id: 'resumes',   label: 'Resumes',      icon: <Icon.FileText /> },
  { id: 'apply',     label: 'Auto Apply',   icon: <Icon.Zap /> },
  { id: 'email',     label: 'Email',        icon: <Icon.Mail /> },
  { id: 'history',   label: 'History',      icon: <Icon.TrendingUp /> },
]

export default function Dashboard() {
  const { user, logout }             = useAuth()
  const { success, error: toastErr, info } = useToast()
  const navigate                     = useNavigate()

  const [activeTab,    setActiveTab]    = useState('overview')
  const [sidebarOpen,  setSidebarOpen]  = useState(false)
  const [dashData,     setDashData]     = useState(null)
  const [resumes,      setResumes]      = useState([])
  const [pageLoading,  setPageLoading]  = useState(true)
  const [uploading,    setUploading]    = useState(false)
  const [dragover,     setDragover]     = useState(false)

  // Auto-apply state
  const [jd,           setJd]           = useState('')
  const [autoSend,     setAutoSend]     = useState(false)
  const [applying,     setApplying]     = useState(false)
  const [applyResult,  setApplyResult]  = useState(null)
  const [oauthConfig,  setOauthConfig]  = useState({ google_oauth_enabled: false, outlook_oauth_enabled: false })
  const [jdFile,       setJdFile]       = useState(null)
  const [uploadingJd,  setUploadingJd]  = useState(false)
  // Editable draft
  const [draftSubject, setDraftSubject] = useState('')
  const [draftBody,    setDraftBody]    = useState('')
  const [sendingDraft, setSendingDraft] = useState(false)
  // Full application history
  const [applications, setApplications] = useState([])

  const fileRef = useRef(null)

  /* ── Fetch dashboard data ── */
  const fetchDashboard = useCallback(async () => {
    try {
      const res = await api.get('/dashboard')
      setDashData(res.data.data)
    } catch {
      // silently ignore; stats will show zeros
    }
  }, [])

  const fetchResumes = useCallback(async () => {
    try {
      const res = await api.get('/resumes')
      setResumes(res.data.data ?? [])
    } catch {
      // ignore
    }
  }, [])

  const fetchApplications = useCallback(async () => {
    try {
      const res = await api.get('/applications')
      setApplications(res.data.data ?? [])
    } catch {
      // ignore
    }
  }, [])

  useEffect(() => {
    if (!user) { navigate('/login'); return }
    Promise.all([fetchDashboard(), fetchResumes(), fetchApplications()]).finally(() => setPageLoading(false))
    // Fetch OAuth config to know which buttons to show
    fetch('/api/auth/config').then((r) => r.json()).then(setOauthConfig).catch(() => {})
  }, [user]) // eslint-disable-line react-hooks/exhaustive-deps

  /* ── Resume upload ── */
  const uploadFile = async (file) => {
    if (!file || file.type !== 'application/pdf') {
      toastErr('Invalid file', 'Only PDF files are supported.')
      return
    }
    setUploading(true)
    const fd = new FormData()
    fd.append('file', file)
    try {
      await api.post('/upload-resume', fd, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      success('Resume uploaded', file.name)
      await fetchResumes()
      await fetchDashboard()
    } catch (e) {
      toastErr('Upload failed', e.response?.data?.detail || 'Please try again.')
    } finally {
      setUploading(false)
    }
  }

  const handleFileInput = (e) => uploadFile(e.target.files?.[0])

  const handleDrop = (e) => {
    e.preventDefault()
    setDragover(false)
    uploadFile(e.dataTransfer.files?.[0])
  }

  const handleDelete = async (filename) => {
    if (!confirm(`Delete "${filename}"?`)) return
    try {
      await api.delete(`/resumes/${encodeURIComponent(filename)}`)
      success('Deleted', filename)
      await fetchResumes()
      await fetchDashboard()
    } catch {
      toastErr('Delete failed', 'Could not remove the resume.')
    }
  }

  /* ── JD file upload ── */
  const handleJdFileUpload = async (file) => {
    if (!file) return
    
    const allowedTypes = ['application/pdf', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document', 'text/plain']
    const allowedExtensions = ['.pdf', '.docx', '.txt']
    const fileExt = '.' + file.name.split('.').pop().toLowerCase()
    
    if (!allowedExtensions.includes(fileExt)) {
      toastErr('Invalid file type', 'Only PDF, DOCX, and TXT files are supported.')
      return
    }
    
    if (file.size > 10 * 1024 * 1024) { // 10MB
      toastErr('File too large', 'Maximum file size is 10MB.')
      return
    }
    
    setUploadingJd(true)
    const fd = new FormData()
    fd.append('file', file)
    
    try {
      const res = await api.post('/upload-jd', fd, {
        headers: { 'Content-Type': 'multipart/form-data' },
      })
      
      setJd(res.data.extracted_text)
      setJdFile(file.name)
      success('JD uploaded', `Extracted ${res.data.extracted_text.length} characters from ${file.name}`)
    } catch (e) {
      toastErr('Upload failed', e.response?.data?.detail || 'Failed to parse job description file.')
    } finally {
      setUploadingJd(false)
    }
  }

  const handleJdFileInput = (e) => {
    const file = e.target.files?.[0]
    if (file) handleJdFileUpload(file)
  }

  const handleJdDrop = (e) => {
    e.preventDefault()
    setDragover(false)
    const file = e.dataTransfer.files?.[0]
    if (file) handleJdFileUpload(file)
  }

  const clearJdFile = () => {
    setJdFile(null)
    setJd('')
  }

  /* ── Auto apply ── */
  const handleAutoApply = async () => {
    if (!jd.trim()) { toastErr('Missing JD', 'Paste a job description first.'); return }
    if (!resumes.length) { toastErr('No resumes', 'Upload at least one resume.'); return }
    if (autoSend && !user.google_connected && !user.outlook_connected) {
      toastErr('No email connected', 'Connect Gmail or Outlook to auto-send.')
      return
    }

    setApplying(true)
    setApplyResult(null)
    setDraftSubject('')
    setDraftBody('')
    try {
      const res = await api.post('/auto-apply', { job_description: jd, auto_send: autoSend })
      const d = res.data.data
      setApplyResult(d)
      setDraftSubject(d.email?.subject ?? '')
      setDraftBody(d.email?.body ?? '')
      success(
        'Draft ready!',
        `${d.job_analysis?.role ?? 'Role'} at ${d.job_analysis?.company ?? 'Company'}`
      )
      if (!autoSend) {
        setJd('')
        setJdFile(null)
      }
      await fetchDashboard()
      await fetchApplications()
    } catch (e) {
      toastErr('Auto-apply failed', e.response?.data?.detail || 'Something went wrong.')
    } finally {
      setApplying(false)
    }
  }

  const handleSendDraft = async () => {
    if (!applyResult) return
    if (!user?.google_connected && !user?.outlook_connected) {
      toastErr('No email connected', 'Connect Gmail or Outlook in the Email tab first.')
      return
    }
    setSendingDraft(true)
    try {
      const provider = user.google_connected ? 'gmail' : 'outlook'
      await api.post('/send-email', {
        job_details: {
          ...applyResult.job_analysis,
          email: applyResult.job_analysis?.email,
          subject: draftSubject,
          body: draftBody,
          resume_file: applyResult.matched_resume?.filename,
        },
        resume_content: '',
        user_profile: { name: user.name, email: user.email },
        email_provider: provider,
        access_token: '',   // backend pulls from stored token
      })
      success('Email sent!', `Application sent to ${applyResult.job_analysis?.company}`)
      setApplyResult((prev) => ({ ...prev, sent: true }))
      await fetchDashboard()
      await fetchApplications()
    } catch (e) {
      toastErr('Send failed', e.response?.data?.detail || 'Could not send email.')
    } finally {
      setSendingDraft(false)
    }
  }

  /* ── OAuth connect ── */
  const connectGoogle = async () => {
    try {
      const res = await fetch('/api/auth/google')
      const d = await res.json()
      window.location.href = d.auth_url
    } catch { toastErr('Error', 'Could not connect to Google.') }
  }

  const connectOutlook = async () => {
    try {
      const res = await fetch('/api/auth/outlook')
      const d = await res.json()
      window.location.href = d.auth_url
    } catch { toastErr('Error', 'Could not connect to Outlook.') }
  }

  /* ── Derived stats ── */
  const stats = dashData?.statistics ?? {}
  const recentApps = dashData?.recent_applications ?? []
  const initials = user?.name
    ? user.name.split(' ').map((n) => n[0]).join('').toUpperCase().slice(0, 2)
    : '??'

  /* ── Loading skeleton ── */
  if (pageLoading) {
    return (
      <div className="dashboard">
        <aside className="sidebar">
          <div className="sidebar__logo">
            <div className="sidebar__logo-icon"><Icon.Layers /></div>
            <span className="sidebar__logo-text">AI Job Agent</span>
          </div>
        </aside>
        <div className="dashboard__main">
          <div className="topbar" />
          <div className="dashboard__content">
            <div className="stats-grid">
              {[1,2,3,4].map((i) => (
                <div key={i} className="stat-card">
                  <div className="skeleton" style={{width:48,height:48,borderRadius:12,flexShrink:0}} />
                  <div style={{flex:1,display:'flex',flexDirection:'column',gap:8}}>
                    <div className="skeleton skeleton--title" style={{width:'60%'}} />
                    <div className="skeleton skeleton--text"  style={{width:'80%'}} />
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="dashboard">
      {/* ── Mobile overlay ── */}
      {sidebarOpen && (
        <div className="sidebar-overlay" onClick={() => setSidebarOpen(false)} />
      )}

      {/* ════════════════════ SIDEBAR ════════════════════ */}
      <aside className={`sidebar${sidebarOpen ? ' open' : ''}`}>
        <div className="sidebar__logo">
          <div className="sidebar__logo-icon"><Icon.Layers /></div>
          <span className="sidebar__logo-text">
            AI Job <span className="sidebar__logo-badge">AI</span>
          </span>
        </div>

        <nav className="sidebar__nav" aria-label="Main navigation">
          <div className="sidebar__nav-section">
            <p className="sidebar__nav-heading">Main</p>
            {TABS.map((tab) => (
              <button
                key={tab.id}
                className={`sidebar__nav-item${activeTab === tab.id ? ' active' : ''}`}
                onClick={() => { setActiveTab(tab.id); setSidebarOpen(false) }}
              >
                {tab.icon}
                {tab.label}
                {tab.id === 'resumes'  && resumes.length > 0 && (
                  <span className="sidebar__nav-badge">{resumes.length}</span>
                )}
                {tab.id === 'history'  && recentApps.length > 0 && (
                  <span className="sidebar__nav-badge">{recentApps.length}</span>
                )}
              </button>
            ))}
          </div>
        </nav>

        <div className="sidebar__user">
          <div className="sidebar__user-avatar">{initials}</div>
          <div className="sidebar__user-info">
            <p className="sidebar__user-name">{user?.name}</p>
            <p className="sidebar__user-email">{user?.email}</p>
          </div>
          <button
            className="sidebar__logout"
            onClick={() => { logout(); navigate('/login') }}
            title="Sign out"
          >
            <Icon.Logout />
          </button>
        </div>
      </aside>

      {/* ════════════════════ MAIN ════════════════════ */}
      <div className="dashboard__main">
        {/* Top bar */}
        <header className="topbar">
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
            <button
              className="topbar__hamburger"
              onClick={() => setSidebarOpen((o) => !o)}
              aria-label={sidebarOpen ? 'Close menu' : 'Open menu'}
            >
              {sidebarOpen ? <Icon.X /> : <Icon.Menu />}
            </button>
            <h1 className="topbar__title">
              {TABS.find((t) => t.id === activeTab)?.label ?? 'Dashboard'}
            </h1>
          </div>

          <div className="topbar__right">
            <p className="topbar__greeting">
              Good {getTimeOfDay()},{' '}
              <strong>{user?.name?.split(' ')[0]}</strong> 👋
            </p>
          </div>
        </header>

        {/* Content */}
        <main className="dashboard__content">

          {/* ══ OVERVIEW TAB ══ */}
          {activeTab === 'overview' && (
            <>
              {/* Stats */}
              <div className="stats-grid">
                <StatCard
                  icon={<Icon.FileText />} theme="indigo"
                  value={stats.total_resumes ?? resumes.length ?? 0}
                  label="Total Resumes"
                  trend={resumes.length > 0 ? `${resumes.length} uploaded` : 'Upload one to start'}
                  trendUp={resumes.length > 0}
                />
                <StatCard
                  icon={<Icon.TrendingUp />} theme="violet"
                  value={stats.total_applications ?? 0}
                  label="Applications"
                  trend={stats.total_applications > 0 ? 'All time' : 'Start applying'}
                  trendUp={stats.total_applications > 0}
                />
                <StatCard
                  icon={<Icon.Mail />} theme="emerald"
                  value={stats.sent_applications ?? 0}
                  label="Emails Sent"
                  trend={stats.sent_applications > 0 ? 'Sent via AI' : 'Connect email first'}
                  trendUp={stats.sent_applications > 0}
                />
                <StatCard
                  icon={<Icon.Link />} theme="amber"
                  value={
                    (user?.google_connected ? 1 : 0) +
                    (user?.outlook_connected ? 1 : 0)
                  }
                  label="Connected Accounts"
                  trend={
                    user?.google_connected && user?.outlook_connected
                      ? 'Gmail + Outlook'
                      : user?.google_connected
                      ? 'Gmail active'
                      : user?.outlook_connected
                      ? 'Outlook active'
                      : 'None connected'
                  }
                  trendUp={user?.google_connected || user?.outlook_connected}
                />
              </div>

              {/* Recent + quick panels */}
              <div className="dashboard-grid">
                <RecentApplications apps={recentApps} onTabSwitch={setActiveTab} />
                <QuickActions onTabSwitch={setActiveTab} resumes={resumes} user={user} />
              </div>
            </>
          )}

          {/* ══ RESUMES TAB ══ */}
          {activeTab === 'resumes' && (
            <div className="dashboard-grid">
              <div className="card" style={{ gridColumn: '1 / -1' }}>
                <div className="card__header">
                  <div className="card__header-left">
                    <div className="card__header-icon"><Icon.FileText /></div>
                    <div>
                      <p className="card__title">My Resumes</p>
                      <p className="card__subtitle">
                        {resumes.length} PDF{resumes.length !== 1 ? 's' : ''} uploaded
                      </p>
                    </div>
                  </div>
                  <button className="btn btn--primary" onClick={() => fileRef.current?.click()}>
                    <Icon.Upload />
                    Upload PDF
                  </button>
                  <input
                    ref={fileRef}
                    type="file"
                    accept=".pdf"
                    style={{ display: 'none' }}
                    onChange={handleFileInput}
                  />
                </div>

                <div className="card__body">
                  {/* Drop zone */}
                  <div
                    className={`upload-zone${dragover ? ' dragover' : ''}`}
                    style={{ marginBottom: resumes.length ? '1.25rem' : 0 }}
                    onDragOver={(e) => { e.preventDefault(); setDragover(true) }}
                    onDragLeave={() => setDragover(false)}
                    onDrop={handleDrop}
                    onClick={() => fileRef.current?.click()}
                    role="button"
                    tabIndex={0}
                    onKeyDown={(e) => e.key === 'Enter' && fileRef.current?.click()}
                    aria-label="Upload resume PDF"
                  >
                    {uploading ? (
                      <div style={{ display: 'flex', justifyContent: 'center' }}>
                        <div className="btn-spinner" style={{ borderColor: 'rgba(99,102,241,0.3)', borderTopColor: '#6366f1', width: 28, height: 28 }} />
                      </div>
                    ) : (
                      <>
                        <div className="upload-zone__icon"><Icon.Upload /></div>
                        <p className="upload-zone__text">Drop PDF here or click to browse</p>
                        <p className="upload-zone__sub">Supports .pdf — max 10 MB</p>
                      </>
                    )}
                  </div>

                  {resumes.length > 0 ? (
                    <div className="resume-list">
                      {resumes.map((r, i) => (
                        <div key={r.filename} className="resume-item" style={{ animationDelay: `${i * 0.06}s` }}>
                          <div className="resume-item__icon"><Icon.FileText /></div>
                          <div className="resume-item__info">
                            <p className="resume-item__name">{r.filename}</p>
                            <p className="resume-item__meta">
                              {(r.size / 1024).toFixed(1)} KB
                              {r.uploaded && ` · ${new Date(r.uploaded * 1000).toLocaleDateString()}`}
                            </p>
                          </div>
                          <button
                            className="btn btn--danger btn--icon"
                            onClick={() => handleDelete(r.filename)}
                            title="Delete"
                          >
                            <Icon.Trash />
                          </button>
                        </div>
                      ))}
                    </div>
                  ) : (
                    <div className="empty-state">
                      <div className="empty-state__icon"><Icon.FileText /></div>
                      <p className="empty-state__title">No resumes yet</p>
                      <p className="empty-state__sub">Upload your first PDF to get started with AI matching</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* ══ AUTO APPLY TAB ══ */}
          {activeTab === 'apply' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1.5rem' }}>

              {/* ── Top row: JD input ── */}
              <div className="card">
                <div className="card__header">
                  <div className="card__header-left">
                    <div className="card__header-icon" style={{ background: '#ede9fe', color: '#7c3aed' }}>
                      <Icon.Zap />
                    </div>
                    <div>
                      <p className="card__title">Auto Apply</p>
                      <p className="card__subtitle">Paste JD or upload file (PDF, DOCX, TXT) — AI matches your resume and drafts the email</p>
                    </div>
                  </div>
                </div>
                <div className="card__body">
                  {/* JD File Upload */}
                  <div 
                    className={`jd-upload-zone ${dragover ? 'jd-upload-zone--dragover' : ''}`}
                    onDragOver={(e) => { e.preventDefault(); setDragover(true) }}
                    onDragLeave={() => setDragover(false)}
                    onDrop={handleJdDrop}
                  >
                    <input
                      ref={fileRef}
                      type="file"
                      accept=".pdf,.docx,.txt"
                      onChange={handleJdFileInput}
                      style={{ display: 'none' }}
                    />
                    <div className="jd-upload-zone__content">
                      {jdFile ? (
                        <div className="jd-upload-zone__file">
                          <Icon.FileText />
                          <span>{jdFile}</span>
                          <button 
                            className="jd-upload-zone__clear"
                            onClick={clearJdFile}
                            type="button"
                          >
                            <Icon.X />
                          </button>
                        </div>
                      ) : (
                        <>
                          <Icon.Upload />
                          <div>
                            <p className="jd-upload-zone__title">Upload JD file</p>
                            <p className="jd-upload-zone__subtitle">PDF, DOCX, or TXT (max 10MB)</p>
                          </div>
                          <button 
                            className="btn btn--secondary"
                            onClick={() => fileRef.current?.click()}
                            type="button"
                            disabled={uploadingJd}
                          >
                            {uploadingJd ? 'Processing...' : 'Choose File'}
                          </button>
                        </>
                      )}
                    </div>
                  </div>

                  {/* JD Text Input */}
                  <textarea
                    className="auto-apply__textarea"
                    placeholder="Or paste the full job description here…&#10;&#10;AI will analyse the role, match your best resume, and generate a personalised cover email draft."
                    value={jd}
                    onChange={(e) => setJd(e.target.value)}
                    rows={7}
                  />
                  
                  <div className="auto-apply__options">
                    <label className="toggle-label" htmlFor="auto-send-toggle">
                      <Toggle id="auto-send-toggle" checked={autoSend} onChange={(e) => setAutoSend(e.target.checked)} />
                      Auto-send after generating
                    </label>
                    {autoSend && !user?.google_connected && !user?.outlook_connected && (
                      <span style={{ fontSize: '0.8125rem', color: '#d97706' }}>⚠ Connect Gmail or Outlook first</span>
                    )}
                  </div>
                  <button
                    className="btn btn--primary btn--lg btn--full"
                    onClick={handleAutoApply}
                    disabled={applying || !jd.trim()}
                  >
                    {applying
                      ? <><span className="btn-spinner" /> Analysing &amp; generating draft…</>
                      : <><Icon.Zap /> Generate Draft</>
                    }
                  </button>
                </div>
              </div>

              {/* ── Draft editor — shown after AI runs ── */}
              {applyResult && (
                <div className="card" style={{ animation: 'fadeInUp 0.4s both' }}>
                  <div className="card__header">
                    <div className="card__header-left">
                      <div className="card__header-icon" style={{ background: '#d1fae5', color: '#059669' }}>
                        <Icon.Mail />
                      </div>
                      <div>
                        <p className="card__title">Email Draft</p>
                        <p className="card__subtitle">
                          {applyResult.job_analysis?.role} at {applyResult.job_analysis?.company}
                          {' · '}
                          <span style={{ color: '#6366f1', fontWeight: 600 }}>
                            {applyResult.matched_resume?.filename}
                          </span>
                          {' '}
                          <ScoreBadge score={applyResult.matched_resume?.score} />
                        </p>
                      </div>
                    </div>
                    {applyResult.sent
                      ? <span className="status-pill status-pill--sent"><Icon.CheckCircle /> Sent</span>
                      : <span className="status-pill status-pill--pending"><Icon.Clock /> Draft</span>
                    }
                  </div>

                  <div className="card__body" style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
                    {/* Subject line */}
                    <div>
                      <label style={{ display: 'block', fontSize: '0.8125rem', fontWeight: 600, color: '#475569', marginBottom: '0.375rem' }}>
                        Subject
                      </label>
                      <input
                        type="text"
                        value={draftSubject}
                        onChange={(e) => setDraftSubject(e.target.value)}
                        style={{
                          width: '100%', padding: '0.625rem 0.875rem',
                          border: '1.5px solid #e2e8f0', borderRadius: '8px',
                          fontSize: '0.9375rem', color: '#1e293b', background: '#f8fafc',
                          outline: 'none', transition: 'border-color 200ms',
                          boxSizing: 'border-box',
                        }}
                        onFocus={(e) => { e.target.style.borderColor = '#6366f1'; e.target.style.boxShadow = '0 0 0 3px rgba(99,102,241,0.12)' }}
                        onBlur={(e)  => { e.target.style.borderColor = '#e2e8f0'; e.target.style.boxShadow = 'none' }}
                        placeholder="Email subject…"
                      />
                    </div>

                    {/* Email body */}
                    <div>
                      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.375rem' }}>
                        <label style={{ fontSize: '0.8125rem', fontWeight: 600, color: '#475569' }}>
                          Email Body
                        </label>
                        <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>
                          {draftBody.length} chars · {draftBody.split(/\s+/).filter(Boolean).length} words
                        </span>
                      </div>
                      <textarea
                        value={draftBody}
                        onChange={(e) => setDraftBody(e.target.value)}
                        rows={16}
                        style={{
                          width: '100%', padding: '0.875rem 1rem',
                          border: '1.5px solid #e2e8f0', borderRadius: '10px',
                          fontSize: '0.9rem', color: '#1e293b', background: '#f8fafc',
                          fontFamily: 'inherit', lineHeight: 1.7, resize: 'vertical',
                          outline: 'none', transition: 'border-color 200ms, box-shadow 200ms',
                          boxSizing: 'border-box',
                        }}
                        onFocus={(e) => { e.target.style.borderColor = '#6366f1'; e.target.style.background = '#fff'; e.target.style.boxShadow = '0 0 0 3px rgba(99,102,241,0.1)' }}
                        onBlur={(e)  => { e.target.style.borderColor = '#e2e8f0'; e.target.style.background = '#f8fafc'; e.target.style.boxShadow = 'none' }}
                        placeholder="Email body…"
                      />
                    </div>

                    {/* Action buttons */}
                    <div style={{ display: 'flex', gap: '0.75rem', flexWrap: 'wrap' }}>
                      {!applyResult.sent && (
                        <button
                          className="btn btn--primary btn--lg"
                          onClick={handleSendDraft}
                          disabled={sendingDraft || (!user?.google_connected && !user?.outlook_connected)}
                          title={!user?.google_connected && !user?.outlook_connected ? 'Connect an email account first' : ''}
                          style={{ flex: 1, minWidth: 160 }}
                        >
                          {sendingDraft
                            ? <><span className="btn-spinner" /> Sending…</>
                            : <><Icon.Mail /> Send Email</>
                          }
                        </button>
                      )}
                      <button
                        className="btn btn--secondary"
                        onClick={() => {
                          navigator.clipboard?.writeText(`Subject: ${draftSubject}\n\n${draftBody}`)
                          success('Copied', 'Draft copied to clipboard')
                        }}
                        style={{ flex: 1, minWidth: 130 }}
                      >
                        <svg viewBox="0 0 20 20" fill="currentColor" style={{ width: 16, height: 16 }}>
                          <path d="M8 3a1 1 0 011-1h2a1 1 0 110 2H9a1 1 0 01-1-1z"/>
                          <path d="M6 3a2 2 0 00-2 2v11a2 2 0 002 2h8a2 2 0 002-2V5a2 2 0 00-2-2 3 3 0 01-3 3H9a3 3 0 01-3-3z"/>
                        </svg>
                        Copy Draft
                      </button>
                      <button
                        className="btn btn--ghost"
                        onClick={() => { setApplyResult(null); setDraftSubject(''); setDraftBody('') }}
                        style={{ minWidth: 100 }}
                      >
                        Clear
                      </button>
                    </div>

                    {!user?.google_connected && !user?.outlook_connected && (
                      <div style={{ padding: '0.75rem 1rem', background: '#fef3c7', borderRadius: 10, border: '1px solid #fde68a', fontSize: '0.875rem', color: '#92400e' }}>
                        <strong>To send this email:</strong> go to the{' '}
                        <button
                          onClick={() => setActiveTab('email')}
                          style={{ background: 'none', border: 'none', color: '#6366f1', fontWeight: 600, cursor: 'pointer', padding: 0, fontSize: 'inherit' }}
                        >
                          Email tab
                        </button>
                        {' '}and connect Gmail or Outlook first.
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          )}

          {/* ══ EMAIL TAB ══ */}
          {activeTab === 'email' && (
            <div className="dashboard-grid">
              <div className="card" style={{ gridColumn: '1 / -1', maxWidth: 640 }}>
                <div className="card__header">
                  <div className="card__header-left">
                    <div className="card__header-icon"><Icon.Mail /></div>
                    <div>
                      <p className="card__title">Email Connections</p>
                      <p className="card__subtitle">Connect an account to auto-send applications</p>
                    </div>
                  </div>
                </div>

                <div className="card__body">
                  <div className="connections-list">
                    {/* Gmail */}
                    <div className="connection-item">
                      <div className="connection-item__logo connection-item__logo--google">
                        <Icon.Google />
                      </div>
                      <div className="connection-item__info">
                        <p className="connection-item__name">Gmail</p>
                        <p className={`connection-item__status connection-item__status--${user?.google_connected ? 'connected' : 'disconnected'}`}>
                          <span className={`connection-item__dot connection-item__dot--${user?.google_connected ? 'connected' : 'disconnected'}`} />
                          {user?.google_connected ? 'Connected' : 'Not connected'}
                        </p>
                      </div>
                      {user?.google_connected ? (
                        <span className="status-pill status-pill--sent">
                          <Icon.CheckCircle /> Active
                        </span>
                      ) : oauthConfig.google_oauth_enabled ? (
                        <button className="btn btn--secondary" onClick={connectGoogle}>
                          Connect
                        </button>
                      ) : (
                        <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Not configured</span>
                      )}
                    </div>

                    {/* Outlook */}
                    <div className="connection-item">
                      <div className="connection-item__logo connection-item__logo--outlook">
                        <Icon.Microsoft />
                      </div>
                      <div className="connection-item__info">
                        <p className="connection-item__name">Outlook / Microsoft 365</p>
                        <p className={`connection-item__status connection-item__status--${user?.outlook_connected ? 'connected' : 'disconnected'}`}>
                          <span className={`connection-item__dot connection-item__dot--${user?.outlook_connected ? 'connected' : 'disconnected'}`} />
                          {user?.outlook_connected ? 'Connected' : 'Not connected'}
                        </p>
                      </div>
                      {user?.outlook_connected ? (
                        <span className="status-pill status-pill--sent">
                          <Icon.CheckCircle /> Active
                        </span>
                      ) : oauthConfig.outlook_oauth_enabled ? (
                        <button className="btn btn--secondary" onClick={connectOutlook}>
                          Connect
                        </button>
                      ) : (
                        <span style={{ fontSize: '0.75rem', color: '#94a3b8' }}>Not configured</span>
                      )}
                    </div>
                  </div>

                  {!user?.google_connected && !user?.outlook_connected && (
                    <div
                      style={{
                        marginTop: '1.25rem',
                        padding: '1rem',
                        background: '#fef3c7',
                        borderRadius: 10,
                        border: '1px solid #fde68a',
                        fontSize: '0.875rem',
                        color: '#92400e',
                      }}
                    >
                      {oauthConfig.google_oauth_enabled || oauthConfig.outlook_oauth_enabled ? (
                        <><strong>Tip:</strong> Connect at least one email account above to enable the auto-send feature.</>
                      ) : (
                        <><strong>OAuth not configured.</strong> Add <code>GOOGLE_CLIENT_ID</code> / <code>OUTLOOK_CLIENT_ID</code> to your <code>.env</code> file to enable email sending.</>
                      )}
                    </div>
                  )}
                </div>
              </div>
            </div>
          )}

          {/* ══ HISTORY TAB ══ */}
          {activeTab === 'history' && (
            <div className="history-container">
              {/* Header row */}
              <div className="history-header">
                <div>
                  <h2 className="history-header__title">Application History</h2>
                  <p className="history-header__sub">
                    {applications.length} application{applications.length !== 1 ? 's' : ''} total
                  </p>
                </div>
              </div>

              {applications.length > 0 ? (
                <div className="history-list">
                  {applications.map((app, i) => (
                    <HistoryCard key={app.id ?? i} app={app} index={i} />
                  ))}
                </div>
              ) : (
                <div className="empty-state" style={{ marginTop: '3rem' }}>
                  <div className="empty-state__icon"><Icon.TrendingUp /></div>
                  <p className="empty-state__title">No applications yet</p>
                  <p className="empty-state__sub">Use Auto Apply to start tracking your applications</p>
                  <button className="btn btn--primary" onClick={() => setActiveTab('apply')}>
                    <Icon.Zap /> Start Applying
                  </button>
                </div>
              )}
            </div>
          )}

        </main>
      </div>
    </div>
  )
}

/* ──────────────────────────────────────────────
   Sub-components
────────────────────────────────────────────── */

/* ── History Card ── */
function HistoryCard({ app, index }) {
  const [expanded, setExpanded] = useState(false)

  const fmt = (iso) => {
    if (!iso) return '—'
    const d = new Date(iso)
    return d.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' }) +
      ' · ' + d.toLocaleTimeString('en-GB', { hour: '2-digit', minute: '2-digit' })
  }

  const scoreColor = (s) => {
    if (s == null) return '#94a3b8'
    if (s >= 70) return '#059669'
    if (s >= 40) return '#f59e0b'
    return '#ef4444'
  }

  const scorePct = app.match_score != null
    ? (app.match_score > 1 ? Math.round(app.match_score) : Math.round(app.match_score * 100))
    : null

  return (
    <>
      <div className="hcard" style={{ animationDelay: `${index * 0.05}s` }}>
        {/* ── Top row ── */}
        <div className="hcard__top">
          <div className="hcard__index">{index + 1}</div>

          <div className="hcard__main">
            <div className="hcard__title-row">
              <span className="hcard__role">{app.role ?? 'Unknown role'}</span>
              <span className="hcard__company">{app.company ?? '—'}</span>
            </div>
            <div className="hcard__meta-row">
              <span className="hcard__meta-item">
                <svg viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M6 2a1 1 0 00-1 1v1H4a2 2 0 00-2 2v10a2 2 0 002 2h12a2 2 0 002-2V6a2 2 0 00-2-2h-1V3a1 1 0 10-2 0v1H7V3a1 1 0 00-1-1zm0 5a1 1 0 000 2h8a1 1 0 100-2H6z" clipRule="evenodd"/></svg>
                {fmt(app.created_at)}
              </span>
              {app.resume_file && (
                <span className="hcard__meta-item">
                  <svg viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clipRule="evenodd"/></svg>
                  {app.resume_file}
                </span>
              )}
              {app.recipient_email && (
                <span className="hcard__meta-item">
                  <svg viewBox="0 0 20 20" fill="currentColor"><path d="M2.003 5.884L10 9.882l7.997-3.998A2 2 0 0016 4H4a2 2 0 00-1.997 1.884z"/><path d="M18 8.118l-8 4-8-4V14a2 2 0 002 2h12a2 2 0 002-2V8.118z"/></svg>
                  {app.recipient_email}
                </span>
              )}
            </div>
          </div>

          <div className="hcard__right">
            {scorePct != null && (
              <div className="hcard__score" style={{ color: scoreColor(scorePct), borderColor: scoreColor(scorePct) + '33' }}>
                <span className="hcard__score-num">{scorePct}%</span>
                <span className="hcard__score-label">match</span>
              </div>
            )}
            <StatusPill status={app.email_sent ? 'sent' : app.status ?? 'pending'} />
            <button
              className="hcard__view-btn"
              onClick={() => setExpanded(true)}
              title="View email content"
            >
              <svg viewBox="0 0 20 20" fill="currentColor"><path d="M10 12a2 2 0 100-4 2 2 0 000 4z"/><path fillRule="evenodd" d="M.458 10C1.732 5.943 5.522 3 10 3s8.268 2.943 9.542 7c-1.274 4.057-5.064 7-9.542 7S1.732 14.057.458 10zM14 10a4 4 0 11-8 0 4 4 0 018 0z" clipRule="evenodd"/></svg>
              View Email
            </button>
          </div>
        </div>
      </div>

      {/* ── Modal overlay ── */}
      {expanded && (
        <div className="hcard__modal-overlay" onClick={() => setExpanded(false)}>
          <div className="hcard__modal" onClick={(e) => e.stopPropagation()}>
            {/* Modal header */}
            <div className="hcard__modal-header">
              <div>
                <p className="hcard__modal-title">{app.role ?? 'Unknown role'} — {app.company ?? '—'}</p>
                <p className="hcard__modal-sub">{fmt(app.created_at)}</p>
              </div>
              <button className="hcard__modal-close" onClick={() => setExpanded(false)} aria-label="Close">
                <svg viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M4.293 4.293a1 1 0 011.414 0L10 8.586l4.293-4.293a1 1 0 111.414 1.414L11.414 10l4.293 4.293a1 1 0 01-1.414 1.414L10 11.414l-4.293 4.293a1 1 0 01-1.414-1.414L8.586 10 4.293 5.707a1 1 0 010-1.414z" clipRule="evenodd"/></svg>
              </button>
            </div>

            {/* Meta pills */}
            <div className="hcard__modal-meta">
              {app.recipient_email && (
                <span className="hcard__modal-pill">
                  <svg viewBox="0 0 20 20" fill="currentColor"><path d="M2.003 5.884L10 9.882l7.997-3.998A2 2 0 0016 4H4a2 2 0 00-1.997 1.884z"/><path d="M18 8.118l-8 4-8-4V14a2 2 0 002 2h12a2 2 0 002-2V8.118z"/></svg>
                  To: {app.recipient_email}
                </span>
              )}
              {app.resume_file && (
                <span className="hcard__modal-pill">
                  <svg viewBox="0 0 20 20" fill="currentColor"><path fillRule="evenodd" d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" clipRule="evenodd"/></svg>
                  {app.resume_file}
                </span>
              )}
              {scorePct != null && (
                <span className="hcard__modal-pill" style={{ color: scoreColor(scorePct) }}>
                  ✦ {scorePct}% match
                </span>
              )}
              <StatusPill status={app.email_sent ? 'sent' : app.status ?? 'pending'} />
            </div>

            {/* Email content */}
            {app.email_subject || app.email_body ? (
              <div className="hcard__modal-body">
                {app.email_subject && (
                  <div className="hcard__modal-section">
                    <span className="hcard__email-label">Subject</span>
                    <p className="hcard__modal-subject">{app.email_subject}</p>
                  </div>
                )}
                {app.email_body && (
                  <div className="hcard__modal-section">
                    <span className="hcard__email-label">Email Body</span>
                    <pre className="hcard__email-body">{app.email_body}</pre>
                  </div>
                )}
              </div>
            ) : (
              <div className="hcard__modal-empty">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.5"><path strokeLinecap="round" strokeLinejoin="round" d="M21.75 6.75v10.5a2.25 2.25 0 01-2.25 2.25h-15a2.25 2.25 0 01-2.25-2.25V6.75m19.5 0A2.25 2.25 0 0019.5 4.5h-15a2.25 2.25 0 00-2.25 2.25m19.5 0v.243a2.25 2.25 0 01-1.07 1.916l-7.5 4.615a2.25 2.25 0 01-2.36 0L3.32 8.91a2.25 2.25 0 01-1.07-1.916V6.75"/></svg>
                <p>No email content saved for this application.</p>
                <span>Email content is saved for applications made after the latest update.</span>
              </div>
            )}
          </div>
        </div>
      )}
    </>
  )
}

function StatCard({ icon, theme, value, label, trend, trendUp }) {
  return (
    <div className="stat-card">
      <div className={`stat-card__icon-wrap stat-card__icon-wrap--${theme}`}>{icon}</div>
      <div className="stat-card__body">
        <p className="stat-card__value">{value}</p>
        <p className="stat-card__label">{label}</p>
        {trend && (
          <p className={`stat-card__trend stat-card__trend--${trendUp ? 'up' : 'neutral'}`}>
            {trendUp ? '↑' : '·'} {trend}
          </p>
        )}
      </div>
    </div>
  )
}

function RecentApplications({ apps, onTabSwitch }) {
  return (
    <div className="card">
      <div className="card__header">
        <div className="card__header-left">
          <div className="card__header-icon" style={{ background: '#d1fae5', color: '#059669' }}>
            <Icon.TrendingUp />
          </div>
          <p className="card__title">Recent Applications</p>
        </div>
        <button className="btn btn--ghost" onClick={() => onTabSwitch('history')}>
          View all
        </button>
      </div>
      <div className="card__body card__body--compact">
        {apps.length > 0 ? (
          <div className="applications-list">
            {apps.slice(0, 5).map((app, i) => (
              <div key={app.id ?? i} className="application-item" style={{ animationDelay: `${i * 0.06}s` }}>
                <div className="application-item__rank">{i + 1}</div>
                <div className="application-item__info">
                  <p className="application-item__role">{app.role ?? 'Unknown role'}</p>
                  <p className="application-item__company">{app.company ?? '—'}</p>
                </div>
                <StatusPill status={app.email_sent ? 'sent' : app.status ?? 'pending'} />
              </div>
            ))}
          </div>
        ) : (
          <div className="empty-state">
            <div className="empty-state__icon"><Icon.TrendingUp /></div>
            <p className="empty-state__title">No applications yet</p>
            <p className="empty-state__sub">Hit Auto Apply to start</p>
          </div>
        )}
      </div>
    </div>
  )
}

function QuickActions({ onTabSwitch, resumes, user }) {
  const actions = [
    {
      icon: <Icon.Upload />,
      label: 'Upload Resume',
      sub:   `${resumes.length} uploaded`,
      tab:   'resumes',
      color: '#6366f1',
      bg:    '#e0e7ff',
    },
    {
      icon: <Icon.Zap />,
      label: 'Auto Apply',
      sub:   'AI-powered applications',
      tab:   'apply',
      color: '#7c3aed',
      bg:    '#ede9fe',
    },
    {
      icon: <Icon.Mail />,
      label: 'Connect Email',
      sub:
        user?.google_connected || user?.outlook_connected
          ? 'Account connected'
          : 'Required for auto-send',
      tab:   'email',
      color: '#059669',
      bg:    '#d1fae5',
    },
  ]

  return (
    <div className="card">
      <div className="card__header">
        <div className="card__header-left">
          <div className="card__header-icon"><Icon.Zap /></div>
          <p className="card__title">Quick Actions</p>
        </div>
      </div>
      <div className="card__body card__body--compact" style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
        {actions.map((a) => (
          <button
            key={a.tab}
            className="resume-item"
            onClick={() => onTabSwitch(a.tab)}
            style={{ cursor: 'pointer', border: 'none', background: '#f8fafc', textAlign: 'left' }}
          >
            <div
              className="resume-item__icon"
              style={{ background: `linear-gradient(135deg, ${a.bg}, ${a.bg})`, color: a.color }}
            >
              {a.icon}
            </div>
            <div className="resume-item__info">
              <p className="resume-item__name">{a.label}</p>
              <p className="resume-item__meta">{a.sub}</p>
            </div>
            <svg viewBox="0 0 20 20" fill="currentColor" style={{ width: 16, height: 16, color: '#94a3b8', flexShrink: 0 }}>
              <path fillRule="evenodd" d="M7.293 14.707a1 1 0 010-1.414L10.586 10 7.293 6.707a1 1 0 011.414-1.414l4 4a1 1 0 010 1.414l-4 4a1 1 0 01-1.414 0z" clipRule="evenodd"/>
            </svg>
          </button>
        ))}
      </div>
    </div>
  )
}

/* ── Helper ── */
function getTimeOfDay() {
  const h = new Date().getHours()
  if (h < 12) return 'morning'
  if (h < 17) return 'afternoon'
  return 'evening'
}
