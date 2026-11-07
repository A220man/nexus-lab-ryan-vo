import '@testing-library/jest-dom'
import { vi } from 'vitest'

// Mock fetch globally
globalThis.fetch = vi.fn() as unknown as typeof fetch

// Mock matchMedia
Object.defineProperty(window, 'matchMedia', {
  writable: true,
  value: vi.fn().mockImplementation(query => ({
    matches: false,
    media: query,
    onchange: null,
    addListener: vi.fn(),
    removeListener: vi.fn(),
    addEventListener: vi.fn(),
    removeEventListener: vi.fn(),
    dispatchEvent: vi.fn(),
  })),
})

// Mock auth module globally for tests
const mockUser = {
  sub: 'test-user',
  email: 'test@example.com',
  name: 'Test User',
  roles: ['viewer'],
}

const mockAuthService = {
  init: vi.fn().mockResolvedValue(undefined),
  isAuthenticated: vi.fn().mockReturnValue(true),
  fetchUserInfo: vi.fn().mockResolvedValue(mockUser),
  getConfig: vi.fn().mockReturnValue({
    demo_mode: true,
    keycloak_url: 'http://localhost:8080',
    keycloak_realm: 'nexus-lab',
    keycloak_client_id: 'nexus-lab',
  }),
  getAccessToken: vi.fn().mockReturnValue('mock-token'),
  getAuthHeader: vi.fn().mockReturnValue('Bearer mock-token'),
  logout: vi.fn().mockResolvedValue(undefined),
  hasRole: vi.fn().mockReturnValue(true),
  hasAnyRole: vi.fn().mockReturnValue(true),
}

vi.mock('../auth', () => ({
  AuthService: vi.fn().mockImplementation(() => mockAuthService),
  User: {
    sub: '',
    email: null,
    name: null,
    roles: [],
  },
  authService: mockAuthService,
}))
