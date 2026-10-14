import { useEffect, useState } from 'react'
import './App.css'

interface HealthResponse {
  status: string
  version: string
  app_name: string
  database: string
  chroma?: string | null
  keycloak?: string | null
}

function App() {
  const [health, setHealth] = useState<HealthResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

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
        setError(err instanceof Error ? err.message : 'Unknown error')
      } finally {
        setLoading(false)
      }
    }

    fetchHealth()
    const interval = setInterval(fetchHealth, 30000)
    return () => clearInterval(interval)
  }, [])

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

  return (
    <div className="app">
      <header className="app-header">
        <h1>nexus-lab-ryan-vo</h1>
        <p className="subtitle">Persistent Context Across Sessions for Every Agent</p>
      </header>

      <main className="app-main">
        <section className="health-card">
          <h2>System Health</h2>

          {loading && <p className="loading">Checking services...</p>}

          {error && (
            <div className="error">
              <strong>Failed to load health:</strong> {error}
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

        <section className="info-card">
          <h2>Quick Links</h2>
          <ul>
            <li><a href="/api/docs" target="_blank" rel="noopener noreferrer">API Documentation</a></li>
            <li><a href="https://github.com/A220man/nexus-lab-ryan-vo" target="_blank" rel="noopener noreferrer">GitHub Repository</a></li>
            <li><a href="https://github.com/A220man/nexus-lab-ryan-vo/issues" target="_blank" rel="noopener noreferrer">Issue Tracker</a></li>
          </ul>
        </section>
      </main>

      <footer className="app-footer">
        <p>Ryan Vo | AI & Machine Learning</p>
        <p>MIT License — Copyright (c) 2026 Ryan Vo <ryandtvo@gmail.com></p>
      </footer>
    </div>
  )
}

export default App