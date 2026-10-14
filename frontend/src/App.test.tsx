import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi, describe, it, expect, beforeEach, afterEach } from 'vitest'
import App from '../App'

describe('App', () => {
  beforeEach(() => {
    vi.resetAllMocks()
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
    })

    render(<App />)

    await waitFor(() => {
      expect(screen.getByText('OK')).toBeInTheDocument()
    })

    expect(screen.getByText('1.0.0')).toBeInTheDocument()
    expect(screen.getByText('DATABASE')).toBeInTheDocument()
    expect(screen.getByText('CHROMADB')).toBeInTheDocument()
    expect(screen.getByText('KEYCLOAK')).toBeInTheDocument()
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
    })

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
    })

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
    expect(screen.getByText('MIT License — Copyright (c) 2026 Ryan Vo <ryandtvo@gmail.com>')).toBeInTheDocument()
  })
})