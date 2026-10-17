import { render, screen, waitFor } from '@testing-library/react'
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest'
import App from "./App"

describe('App', () => {
  beforeEach(() => {
    vi.resetAllMocks()
    vi.mocked(fetch).mockImplementation(async (input: RequestInfo | URL) => {
      const url = typeof input === 'string' ? input : input.toString()
      if (url.includes('/api/sessions')) {
        return {
          ok: true,
          json: async () => [],
        } as Response
      }
      return {
        ok: true,
        json: async () => ({
          status: 'ok',
          version: '1.0.1',
          app_name: 'nexus-lab-ryan-vo',
          database: 'ok',
        }),
      } as Response
    })
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
    expect(screen.getByText('Checking services...')).toBeInTheDocument()
  })

  it('displays health data when fetch succeeds', async () => {
    const mockHealth = {
      status: 'ok',
      version: '1.0.0',
      app_name: 'nexus-lab-ryan-vo',
      database: 'ok',
      chroma: 'ok',
      keycloak: 'ok',
    }

    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => mockHealth,
    } as Response)

    render(<App />)

    await waitFor(() => {
      const overallStatusLabel = screen.getByText('Overall Status')
      expect(overallStatusLabel).toBeInTheDocument()
      const overallStatusValue = overallStatusLabel.closest('.health-item')?.querySelector('.health-value')
      expect(overallStatusValue).toHaveTextContent('OK')
    })

    expect(screen.getByText('1.0.0')).toBeInTheDocument()
    expect(screen.getByText('Database')).toBeInTheDocument()
    expect(screen.getByText('ChromaDB')).toBeInTheDocument()
    expect(screen.getByText('Keycloak')).toBeInTheDocument()
  })

  it('displays error when fetch fails', async () => {
    vi.mocked(fetch).mockRejectedValueOnce(new Error('Network error'))

    render(<App />)

    await waitFor(() => {
      expect(screen.getByText('Failed to load health:')).toBeInTheDocument()
    })
    expect(screen.getByText('Network error')).toBeInTheDocument()
  })

  it('displays degraded status with warning color', async () => {
    const mockHealth = {
      status: 'degraded',
      version: '1.0.0',
      app_name: 'nexus-lab-ryan-vo',
      database: 'ok',
      chroma: 'unavailable',
      keycloak: 'ok',
    }

    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => mockHealth,
    } as Response)

    render(<App />)

    await waitFor(() => {
      expect(screen.getByText('DEGRADED')).toBeInTheDocument()
    })

    const degradedElement = screen.getByText('DEGRADED')
    expect(degradedElement).toHaveStyle({ color: '#f59e0b' })
  })

  it('renders quick links section', async () => {
    const mockHealth = {
      status: 'ok',
      version: '1.0.0',
      app_name: 'nexus-lab-ryan-vo',
      database: 'ok',
    }

    vi.mocked(fetch).mockResolvedValueOnce({
      ok: true,
      json: async () => mockHealth,
    } as Response)

    render(<App />)

    await waitFor(() => {
      expect(screen.getByText('Quick Links')).toBeInTheDocument()
    })

    expect(screen.getByRole('link', { name: 'API Documentation' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'GitHub Repository' })).toBeInTheDocument()
    expect(screen.getByRole('link', { name: 'Issue Tracker' })).toBeInTheDocument()
  })

  it('renders footer with author info', () => {
    render(<App />)
    expect(screen.getByText('Ryan Vo | AI & Machine Learning')).toBeInTheDocument()
    // App.tsx uses &mdash; and <> which render as — and <>
    expect(screen.getByText('MIT License — Copyright (c) 2026 Ryan Vo <ryandtvo@gmail.com>')).toBeInTheDocument()
  })
})