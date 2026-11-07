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
        this.accessToken = data.accessToken
        this.refreshToken = data.refreshToken
        this.tokenExpiry = data.tokenExpiry
        this.user = data.user
      }
    } catch {
      this.clearStorage()
    }
  }

  private saveToStorage(): void {
    if (this.accessToken && this.refreshToken && this.tokenExpiry && this.user) {
      localStorage.setItem(AUTH_STORAGE_KEY, JSON.stringify({
        accessToken: this.accessToken,
        refreshToken: this.refreshToken,
        tokenExpiry: this.tokenExpiry,
        user: this.user,
      }))
    }
  }

  private clearStorage(): void {
    this.accessToken = null
    this.refreshToken = null
    this.tokenExpiry = null
    this.user = null
    localStorage.removeItem(AUTH_STORAGE_KEY)
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
    return this.config!
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
    return this.accessToken
  }

  getAuthHeader(): string | null {
    const token = this.getAccessToken()
    return token ? `Bearer ${token}` : null
  }

  async login(redirectUri?: string): Promise<void> {
    const config = await this.fetchConfig()
    if (config.demo_mode) {
      // Demo mode: create demo tokens directly
      const response = await fetch('/api/auth/demo-tokens', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
      })
      if (!response.ok) {
        throw new Error('Failed to create demo tokens')
      }
      const data = await response.json()
      this.accessToken = data.access_token
      this.refreshToken = data.refresh_token
      this.tokenExpiry = Date.now() + data.expires_in * 1000
      await this.fetchUserInfo()
      this.saveToStorage()
      return
    }

    // Production mode: redirect to Keycloak with PKCE
    const codeVerifier = generateCodeVerifier()
    const codeChallenge = generateCodeChallenge(codeVerifier)
    const state = generateState()
    const nonce = generateNonce()

    const params = new URLSearchParams({
      client_id: config.keycloak_client_id,
      redirect_uri: redirectUri || window.location.origin,
      response_type: 'code',
      scope: 'openid profile email',
      code_challenge: codeChallenge,
      code_challenge_method: 'S256',
      state,
      nonce,
    })

    // Store PKCE state
    storeAuthState({
      codeVerifier,
      codeChallenge,
      state,
      nonce,
      redirectUri: redirectUri || window.location.origin,
      createdAt: Date.now(),
    })

    window.location.href = `${config.keycloak_url}/realms/${config.keycloak_realm}/protocol/openid-connect/auth?${params.toString()}`
  }

  async handleCallback(hash: string): Promise<void> {
    const params = new URLSearchParams(hash.slice(1))
    const code = params.get('code')
    const state = params.get('state')
    const error = params.get('error')

    if (error) {
      throw new Error(`OAuth error: ${error}`)
    }

    if (!code || !state) {
      throw new Error('Missing code or state in callback')
    }

    const authState = getAuthState(state)
    if (!authState) {
      throw new Error('Invalid or expired state')
    }

    const config = await this.fetchConfig()
    const tokenResponse = await fetch(`${config.keycloak_url}/realms/${config.keycloak_realm}/protocol/openid-connect/token`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({
        grant_type: 'authorization_code',
        client_id: config.keycloak_client_id,
        code,
        redirect_uri: authState.redirectUri,
        code_verifier: authState.codeVerifier,
      }),
    })

    if (!tokenResponse.ok) {
      const errorData = await tokenResponse.json()
      throw new Error(`Token exchange failed: ${errorData.error_description || errorData.error}`)
    }

    const tokens = await tokenResponse.json()
    this.accessToken = tokens.access_token
    this.refreshToken = tokens.refresh_token
    this.tokenExpiry = Date.now() + tokens.expires_in * 1000

    await this.fetchUserInfo()
    this.saveToStorage()
  }

  async fetchUserInfo(): Promise<User> {
    const token = this.getAccessToken()
    if (!token) {
      throw new Error('Not authenticated')
    }

    const config = await this.fetchConfig()
    const response = await fetch(`${config.keycloak_url}/realms/${config.keycloak_realm}/protocol/openid-connect/userinfo`, {
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
      roles: data.realm_access?.roles || [],
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
        const config = await this.fetchConfig()
        const response = await fetch(`${config.keycloak_url}/realms/${config.keycloak_realm}/protocol/openid-connect/token`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
          body: new URLSearchParams({
            grant_type: 'refresh_token',
            client_id: config.keycloak_client_id,
            refresh_token: this.refreshToken!,
          }),
        })

        if (!response.ok) {
          throw new Error('Token refresh failed')
        }

        const tokens = await response.json()
        this.accessToken = tokens.access_token
        this.refreshToken = tokens.refresh_token
        this.tokenExpiry = Date.now() + tokens.expires_in * 1000
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

    const token = this.getAccessToken()
    if (token) {
      try {
        await fetch(`${config.keycloak_url}/realms/${config.keycloak_realm}/protocol/openid-connect/logout`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
          body: new URLSearchParams({
            client_id: config.keycloak_client_id,
            refresh_token: this.refreshToken || '',
          }),
        })
      } catch {
        // Ignore logout errors
      }
    }
    this.clearStorage()
  }

  hasRole(role: string): boolean {
    return this.user?.roles.includes(role) ?? false
  }

  hasAnyRole(roles: string[]): boolean {
    if (!this.user) return false
    return roles.some((r) => this.user!.roles.includes(r))
  }
}

function generateCodeVerifier(): string {
  const array = new Uint8Array(32)
  crypto.getRandomValues(array)
  return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('')
}

function generateCodeChallenge(codeVerifier: string): string {
  // Simplified for demo - in production use crypto.subtle.digest
  return btoa(codeVerifier).replace(/\+/g, '-').replace(/\//g, '_').replace(/=/g, '')
}

function generateState(): string {
  const array = new Uint8Array(16)
  crypto.getRandomValues(array)
  return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('')
}

function generateNonce(): string {
  const array = new Uint8Array(16)
  crypto.getRandomValues(array)
  return Array.from(array, byte => byte.toString(16).padStart(2, '0')).join('')
}

// In-memory state store for PKCE
interface AuthState {
  codeVerifier: string
  codeChallenge: string
  state: string
  nonce: string
  redirectUri: string
  createdAt: number
}

const authStates: Map<string, AuthState> = new Map()

function storeAuthState(state: AuthState): void {
  authStates.set(state.state, state)
  // Clean up old states
  const now = Date.now()
  for (const [key, value] of authStates.entries()) {
    if (now - value.createdAt > 600000) { // 10 minutes
      authStates.delete(key)
    }
  }
}

function getAuthState(state: string): AuthState | undefined {
  return authStates.get(state)
}

export const authService = new AuthService()
