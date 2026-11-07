import { render, screen, waitFor } from '@testing-library/react'
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest'
import App from "./App"
import { authService } from './auth'

describe('App', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    vi.mocked(fetch).mockImplementation(async (input: RequestInfo | URL) => {
      const url = input.toString()
      if (url.includes('/api/health')) {
        return {
          ok: true,
          json: async () => ({
            status: 'ok',
            version: '1.0.0',
            app_name: 'nexus-lab-ryan-vo',
            database: 'ok',
            chroma: 'ok',
            keycloak: 'ok',
          }),
        } as Response
      }
      if (url.includes('/api/auth/config')) {
        return {
          ok: true,
          json: async () => ({
            demo_mode: true,
            keycloak_url: 'http://localhost:8080',
            keycloak_realm: 'nexus-lab',
            keycloak_client_id: 'nexus-lab',
          }),
        } as Response
      }
      if (url.includes('/api/auth/me')) {
        return {
          ok: true,
          json: async () => ({
            sub: 'test-user',
            email: 'test@example.com',
            name: 'Test User',
            roles: ['viewer'],
          }),
        } as Response
      }
      if (url.includes('/api/sessions')) {
        return {
          ok: true,
          json: async () => [],
        } as Response
      }
      if (url.includes('/api/observations')) {
        return {
          ok: true,
          json: async () => [],
        } as Response
      }
      return {
        ok: true,
        json: async () => ({}),
      } as Response
    })
    // Reset auth service mocks using vi.fn()
    authService.init = vi.fn().mockResolvedValue(undefined)
    authService.isAuthenticated = vi.fn().mockReturnValue(true)
    authService.fetchUserInfo = vi.fn().mockResolvedValue({
      sub: 'test-user',
      email: 'test@example.com',
      name: 'Test User',
      roles: ['viewer'],
    })
    authService.getConfig = vi.fn().mockReturnValue({
      demo_mode: true,
      keycloak_url: 'http://localhost:8080',
      keycloak_realm: 'nexus-lab',
      keycloak_client_id: 'nexus-lab',
    })
    authService.getAccessToken = vi.fn().mockReturnValue('mock-token')
    authService.getAuthHeader = vi.fn().mockReturnValue('Bearer mock-token')
    authService.logout = vi.fn().mockResolvedValue(undefined)
    authService.hasRole = vi.fn().mockReturnValue(true)
    authService.hasAnyRole = vi.fn().mockReturnValue(true)
  })

  afterEach(() => {
    vi.clearAllTimers()
  })

  it('renders app title and subtitle', () => {
    render(<App />)
    expect(screen.getByText('nexus-lab-ryan-vo')).toBeInTheDocument()
    expect(screen.getByText('Persistent Context Across Sessions for Every Agent')).toBeInTheDocument()
  })

  it('shows loading state initially', () => {
    render(<App />)
    expect(screen.getByText('Initializing...')).toBeInTheDocument()
  })

  it('displays health data when fetch succeeds', async () => {
    render(<App />)

    await waitFor(() => {
      const overallStatusLabel = screen.getByText('Overall Status')
      expect(overallStatusLabel).toBeInTheDocument()
    })

    // Use getAllByText since there are multiple "OK" elements
    const okElements = screen.getAllByText('OK')
    expect(okElements.length).toBeGreaterThan(0)
    expect(screen.getByText('1.0.0')).toBeInTheDocument()
    expect(screen.getByText('Database')).toBeInTheDocument()
    expect(screen.getByText('ChromaDB')).toBeInTheDocument()
    expect(screen.getByText('Keycloak')).toBeInTheDocument()
  })

  it('renders quick links section', async () => {
    render(<App />)

    await waitFor(() => {
      expect(screen.getByText('Quick Links')).toBeInTheDocument()
    })
  })

  it('renders footer with author info', async () => {
    render(<App />)

    await waitFor(() => {
      // App.tsx uses &mdash; and <> which render as — and <>
      expect(screen.getByText('Ryan Vo | AI & Machine Learning')).toBeInTheDocument()
      expect(screen.getByText('MIT License — Copyright (c) 2026 Ryan Vo <ryandtvo@gmail.com>')).toBeInTheDocument()
    })
  })
})
