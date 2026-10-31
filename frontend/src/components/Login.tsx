import { useEffect, useState } from 'react'
import { authService } from '../auth'

export function Login() {
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const handleHashChange = async () => {
      const hash = window.location.hash
      if (hash.startsWith('#/callback')) {
        try {
          await authService.handleCallback(hash)
          // Clear hash and reload
          window.history.replaceState({}, document.title, window.location.pathname)
          window.location.reload()
        } catch (err) {
          setError(err instanceof Error ? err.message : 'Login failed')
        } finally {
          setLoading(false)
        }
      } else {
        setLoading(false)
      }
    }

    handleHashChange()
    window.addEventListener('hashchange', handleHashChange)
    return () => window.removeEventListener('hashchange', handleHashChange)
  }, [])

  const handleLogin = async () => {
    setLoading(true)
    setError(null)
    try {
      await authService.login(window.location.origin)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Login failed')
      setLoading(false)
    }
  }

  if (loading) {
    return (
      <div className="login-container">
        <div className="login-card">
          <div className="login-spinner" />
          <p>Loading...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="login-container">
      <div className="login-card">
        <h1>nexus-lab-ryan-vo</h1>
        <p className="subtitle">Persistent Context Across Sessions for Every Agent</p>

        {error && <div className="error">{error}</div>}

        <button className="login-button" onClick={handleLogin} disabled={loading}>
          {loading ? 'Signing in...' : 'Sign in with Keycloak'}
        </button>

        <p className="demo-notice">
          Demo mode: Click to sign in as demo user
        </p>
      </div>
    </div>
  )
}
