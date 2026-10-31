export interface User {
  sub: string
  email: string | null
  name: string | null
  roles: string[]
}

export interface TokenResponse {
  access_token: string
  refresh_token: string
  token_type: string
  expires_in: number
  user: User
}

export interface AuthConfig {
  demo_mode: boolean
  keycloak_url: string
  keycloak_realm: string
  keycloak_client_id: string
}

const AUTH_STORAGE_KEY = 'nexus-lab-auth'
const TOKEN_EXPIRY_BUFFER = 60000 // 1 minute buffer

class AuthService {
  private accessToken: string | null = null
  private refreshToken: string | null = null
  private tokenExpiry: number | null = null
  private user: User | null = null
  private config: AuthConfig | null = null
  private refreshPromise: Promise<void> | null = null

  constructor() {
    this.loadFromStorage()
  }

  private loadFromStorage(): void {
    try {
      const stored = localStorage.getItem(AUTH_STORAGE_KEY)
      if (stored) {
        const data = JSON.parse(stored)
        this.accessToken = data.access_token
        this.refreshToken = data.refresh_token
        this.tokenExpiry = data.expires_at
        this.user = data.user
      }
    } catch {
      // Ignore parse errors
    }
  }

  private saveToStorage(): void {
    if (this.accessToken && this.refreshToken && this.tokenExpiry && this.user) {
      localStorage.setItem(
        AUTH_STORAGE_KEY,
        JSON.stringify({
          access_token: this.accessToken,
          refresh_token: this.refreshToken,
          expires_at: this.tokenExpiry,
          user: this.user,
        })
      )
    }
  }

  private clearStorage(): void {
    localStorage.removeItem(AUTH_STORAGE_KEY)
    this.accessToken = null
    this.refreshToken = null
    this.tokenExpiry = null
    this.user = null
  }

  async init(): Promise<void> {
    await this.fetchConfig()
    // Check if we have a valid token
    if (this.accessToken && this.tokenExpiry && Date.now() < this.tokenExpiry - TOKEN_EXPIRY_BUFFER) {
      return
    }
    // Try to refresh if we have a refresh token
    if (this.refreshToken) {
      try {
        await this.refreshAccessToken()
      } catch {
        this.clearStorage()
      }
    }
  }

  async fetchConfig(): Promise<AuthConfig> {
    if (this.config) return this.config
    const response = await fetch('/api/auth/config')
    if (!response.ok) {
      throw new Error('Failed to fetch auth config')
    }
    this.config = await response.json()
    return this.config
  }

  getConfig(): AuthConfig | null {
    return this.config
  }

  isAuthenticated(): boolean {
    return !!this.accessToken && !!this.tokenExpiry && Date.now() < this.tokenExpiry - TOKEN_EXPIRY_BUFFER
  }

  getUser(): User | null {
    return this.user
  }

  getAccessToken(): string | null {
    if (this.isAuthenticated()) {
      return this.accessToken
    }
    return null
  }

  getAuthHeader(): string | null {
    const token = this.getAccessToken()
    return token ? `Bearer ${token}` : null
  }

  async login(redirectUri?: string): Promise<void> {
    const config = await this.fetchConfig()

    if (config.demo_mode) {
      // Demo mode: get tokens directly
      const response = await fetch(`/api/auth/login${redirectUri ? `?redirect_uri=${encodeURIComponent(redirectUri)}` : ''}`)
      if (!response.ok) {
        throw new Error('Demo login failed')
      }
      // In demo mode, the backend redirects with tokens in fragment
      // This is handled by the callback
      return
    }

    // Production mode: redirect to Keycloak
    const response = await fetch(`/api/auth/login${redirectUri ? `?redirect_uri=${encodeURIComponent(redirectUri)}` : ''}`)
    if (!response.ok) {
      throw new Error('Failed to initiate login')
    }
    const data = await response.json()
    // Redirect to Keycloak
    window.location.href = data.auth_url
  }

  async handleCallback(hash: string): Promise<void> {
    const params = new URLSearchParams(hash.startsWith('#') ? hash.substring(1) : hash)
    const accessToken = params.get('access_token')
    const refreshToken = params.get('refresh_token')
    const expiresIn = params.get('expires_in')
    const error = params.get('error')

    if (error) {
      throw new Error(`Authentication failed: ${error}`)
    }

    if (!accessToken || !refreshToken || !expiresIn) {
      throw new Error('Invalid callback: missing tokens')
    }

    this.accessToken = accessToken
    this.refreshToken = refreshToken
    this.tokenExpiry = Date.now() + parseInt(expiresIn) * 1000

    // Fetch user info
    await this.fetchUserInfo()
    this.saveToStorage()
  }

  async fetchUserInfo(): Promise<User> {
    const token = this.getAccessToken()
    if (!token) {
      throw new Error('Not authenticated')
    }

    const response = await fetch('/api/auth/me', {
      headers: { Authorization: `Bearer ${token}` },
    })

    if (!response.ok) {
      if (response.status === 401) {
        this.clearStorage()
      }
      throw new Error('Failed to fetch user info')
    }

    const data = await response.json()
    this.user = {
      sub: data.sub,
      email: data.email,
      name: data.name,
      roles: data.roles || [],
    }
    return this.user
  }

  async refreshAccessToken(): Promise<void> {
    if (this.refreshPromise) {
      return this.refreshPromise
    }

    if (!this.refreshToken) {
      throw new Error('No refresh token available')
    }

    this.refreshPromise = (async () => {
      try {
        const response = await fetch('/api/auth/refresh', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ refresh_token: this.refreshToken }),
        })

        if (!response.ok) {
          if (response.status === 401) {
            this.clearStorage()
          }
          throw new Error('Token refresh failed')
        }

        const data: TokenResponse = await response.json()
        this.accessToken = data.access_token
        this.refreshToken = data.refresh_token
        this.tokenExpiry = Date.now() + data.expires_in * 1000
        this.user = data.user
        this.saveToStorage()
      } finally {
        this.refreshPromise = null
      }
    })()

    return this.refreshPromise
  }

  async logout(): Promise<void> {
    const config = await this.fetchConfig()

    if (config.demo_mode) {
      this.clearStorage()
      return
    }

    // In production, redirect to Keycloak logout
    const idToken = this.accessToken // Use access token as ID token hint
    const response = await fetch('/api/auth/logout', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${this.accessToken}`,
      },
    })

    if (response.ok) {
      const data = await response.json()
      this.clearStorage()
      if (data.logout_url) {
        window.location.href = data.logout_url
      }
    } else {
      this.clearStorage()
    }
  }

  hasRole(role: string): boolean {
    if (!this.user) return false
    return this.user.roles.includes(role)
  }

  hasAnyRole(roles: string[]): boolean {
    if (!this.user) return false
    return roles.some((r) => this.user!.roles.includes(r))
  }
}

export const authService = new AuthService()
