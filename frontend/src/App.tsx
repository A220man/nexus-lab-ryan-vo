import { useEffect, useState } from 'react'
import './App.css'
import {
  SessionItem,
  ObservationItem,
  CreateSessionPayload,
  CreateObservationPayload,
  fetchSessions,
  createSession,
  deleteSession,
  fetchObservations,
  createObservation,
  searchObservations,
} from './api'
import { SessionList } from './components/SessionList'
import { ObservationView } from './components/ObservationView'
import { Login } from './components/Login'
import { UserMenu } from './components/UserMenu'
import { authService, User } from './auth'

interface HealthResponse {
  status: string
  version: string
  app_name: string
  database: string
  chroma?: string | null
  keycloak?: string | null
}

export function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [healthLoading, setHealthLoading] = useState(true)
  const [healthError, setHealthError] = useState<string | null>(null)

  const [sessions, setSessions] = useState<SessionItem[]>([])
  const [selectedSession, setSelectedSession] = useState<SessionItem | null>(null)
  const [sessionsLoading, setSessionsLoading] = useState(true)

  const [observations, setObservations] = useState<ObservationItem[]>([])
  const [observationsLoading, setObservationsLoading] = useState(false)

  const [user, setUser] = useState<User | null>(null)
  const [authInitialized, setAuthInitialized] = useState(false)

  // Initialize auth
  useEffect(() => {
    const initAuth = async () => {
      try {
        await authService.init()
        if (authService.isAuthenticated()) {
          const userInfo = await authService.fetchUserInfo()
          setUser(userInfo)
        }
      } catch (err) {
        console.error('Auth initialization failed', err)
      } finally {
        setAuthInitialized(true)
      }
    }

    initAuth()
  }, [])

  // Fetch health
  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const response = await fetch('/api/health')
        if (!response.ok) {
          throw new Error(`HTTP ${response.status}`)
        }
        const data = await response.json()
        setHealth(data)
      } catch (err) {
        setHealthError(err instanceof Error ? err.message : 'Unknown error')
      } finally {
        setHealthLoading(false)
      }
    }

    fetchHealth()
    const interval = setInterval(fetchHealth, 30000)
    return () => clearInterval(interval)
  }, [])

  // Load sessions on mount and when auth changes
  useEffect(() => {
    if (authInitialized && authService.isAuthenticated()) {
      loadSessions()
    }
  }, [authInitialized])

  const loadSessions = async () => {
    setSessionsLoading(true)
    try {
      const data = await fetchSessions()
      setSessions(data)
      if (data.length > 0 && !selectedSession) {
        setSelectedSession(data[0])
      }
    } catch (err) {
      console.error('Failed to load sessions', err)
    } finally {
      setSessionsLoading(false)
    }
  }

  // Load observations when selected session changes
  useEffect(() => {
    if (selectedSession) {
      loadObservations(selectedSession.id)
    } else {
      setObservations([])
    }
  }, [selectedSession?.id])

  const loadObservations = async (sessionId: string) => {
    setObservationsLoading(true)
    try {
      const data = await fetchObservations(sessionId)
      setObservations(data)
    } catch (err) {
      console.error('Failed to load observations', err)
    } finally {
      setObservationsLoading(false)
    }
  }

  const handleCreateSession = async (payload: CreateSessionPayload) => {
    const created = await createSession(payload)
    setSessions((prev) => [created, ...prev])
    setSelectedSession(created)
  }

  const handleDeleteSession = async (id: string) => {
    await deleteSession(id)
    setSessions((prev) => prev.filter((s) => s.id !== id))
    if (selectedSession?.id === id) {
      setSelectedSession(null)
    }
  }

  const handleCreateObservation = async (payload: CreateObservationPayload) => {
    if (!selectedSession) return
    const created = await createObservation(selectedSession.id, payload)
    // Update or prepend depending on occurrence count
    setObservations((prev) => {
      const existingIdx = prev.findIndex((o) => o.content_hash === created.content_hash)
      if (existingIdx >= 0) {
        const updated = [...prev]
        updated[existingIdx] = created
        return updated
      }
      return [created, ...prev]
    })
  }

  const handleSearchObservations = async (query: string) => {
    if (!query) {
      if (selectedSession) {
        loadObservations(selectedSession.id)
      }
      return
    }
    setObservationsLoading(true)
    try {
      const results = await searchObservations(query, selectedSession?.project)
      setObservations(results)
    } catch (err) {
      console.error('Search failed', err)
    } finally {
      setObservationsLoading(false)
    }
  }

  const handleLogout = async () => {
    await authService.logout()
    setUser(null)
    setSessions([])
    setSelectedSession(null)
    setObservations([])
    // In demo mode, reload to show login
    if (authService.getConfig()?.demo_mode) {
      window.location.reload()
    }
  }

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'ok':
        return '#22c55e'
      case 'degraded':
        return '#f59e0b'
      case 'failed':
      case 'unavailable':
        return '#ef4444'
      default:
        return '#6b7280'
    }
  }

  // Show login if not authenticated
  if (!authInitialized) {
    return (
      <div className="app">
        <header className="app-header">
          <h1>nexus-lab-ryan-vo</h1>
          <p className="subtitle">Persistent Context Across Sessions for Every Agent</p>
        </header>
        <main className="app-main">
          <div className="login-container">
            <div className="login-card">
              <div className="login-spinner" />
              <p>Initializing...</p>
            </div>
          </div>
        </main>
      </div>
    )
  }

  if (!authService.isAuthenticated()) {
    return <Login />
  }

  return (
    <div className="app">
      <header className="app-header">
        <h1>nexus-lab-ryan-vo</h1>
        <p className="subtitle">Persistent Context Across Sessions for Every Agent</p>
        {user && <UserMenu user={user} onLogout={handleLogout} />}
      </header>

      <main className="app-main">
        <section className="card health-card">
          <h2>System Health</h2>

          {healthLoading && <p className="loading">Checking services...</p>}

          {healthError && (
            <div className="error">
              <strong>Failed to load health:</strong> {healthError}
            </div>
          )}

          {health && (
            <div className="health-grid">
              <div className="health-item">
                <span className="health-label">Overall Status</span>
                <span
                  className="health-value"
                  style={{ color: getStatusColor(health.status) }}
                >
                  {health.status.toUpperCase()}
                </span>
              </div>

              <div className="health-item">
                <span className="health-label">Version</span>
                <span className="health-value">{health.version}</span>
              </div>

              <div className="health-item">
                <span className="health-label">Database</span>
                <span
                  className="health-value"
                  style={{ color: getStatusColor(health.database) }}
                >
                  {health.database.toUpperCase()}
                </span>
              </div>

              {health.chroma && (
                <div className="health-item">
                  <span className="health-label">ChromaDB</span>
                  <span
                    className="health-value"
                    style={{ color: getStatusColor(health.chroma) }}
                  >
                    {health.chroma.toUpperCase()}
                  </span>
                </div>
              )}

              {health.keycloak && (
                <div className="health-item">
                  <span className="health-label">Keycloak</span>
                  <span
                    className="health-value"
                    style={{ color: getStatusColor(health.keycloak) }}
                  >
                    {health.keycloak.toUpperCase()}
                  </span>
                </div>
              )}
            </div>
          )}
        </section>

        <div className="workspace-layout">
          <SessionList
            sessions={sessions}
            selectedSessionId={selectedSession?.id ?? null}
            onSelectSession={setSelectedSession}
            onCreateSession={handleCreateSession}
            onDeleteSession={handleDeleteSession}
            loading={sessionsLoading}
          />

          {selectedSession ? (
            <ObservationView
              session={selectedSession}
              observations={observations}
              onCreateObservation={handleCreateObservation}
              onSearch={handleSearchObservations}
              loading={observationsLoading}
            />
          ) : (
            <section className="card empty-workspace">
              <h2>Agent Observation Workspace</h2>
              <p className="empty-state">Select or create a session to view and record observations.</p>
            </section>
          )}
        </div>

        <section className="card info-card">
          <h2>Quick Links</h2>
          <ul>
            <li>
              <a href="/api/docs" target="_blank" rel="noopener noreferrer">
                API Documentation
              </a>
            </li>
            <li>
              <a href="https://github.com/A220man/nexus-lab-ryan-vo" target="_blank" rel="noopener noreferrer">
                GitHub Repository
              </a>
            </li>
            <li>
              <a href="https://github.com/A220man/nexus-lab-ryan-vo/issues" target="_blank" rel="noopener noreferrer">
                Issue Tracker
              </a>
            </li>
          </ul>
        </section>
      </main>

      <footer className="app-footer">
        <p>Ryan Vo | AI & Machine Learning</p>
        <p>MIT License &mdash; Copyright (c) 2026 Ryan Vo &lt;ryandtvo@gmail.com&gt;</p>
      </footer>
    </div>
  )
}

export default App
