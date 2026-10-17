export interface SessionItem {
  id: string
  project: string
  name: string
  description?: string | null
  status: 'active' | 'completed' | 'failed' | 'archived'
  platform_source?: string | null
  platform_session_id?: string | null
  metadata?: Record<string, unknown> | null
  created_at: string
  updated_at: string
}

export interface ObservationItem {
  id: string
  session_id: string
  type: 'bugfix' | 'feature' | 'refactor' | 'verification' | 'investigation' | 'neutral'
  title: string
  narrative?: string | null
  files_read?: string[] | null
  files_edited?: string[] | null
  tools_used?: string[] | null
  content_hash: string
  occurrence_count: number
  raw_output?: string | null
  metadata?: Record<string, unknown> | null
  created_at: string
  updated_at: string
}

export interface CreateSessionPayload {
  project: string
  name: string
  description?: string
  platform_source?: string
  platform_session_id?: string
  metadata?: Record<string, unknown>
}

export interface CreateObservationPayload {
  title: string
  type?: ObservationItem['type']
  narrative?: string
  files_read?: string[]
  files_edited?: string[]
  tools_used?: string[]
  raw_output?: string
  metadata?: Record<string, unknown>
}

const API_BASE = '/api'

export async function fetchSessions(project?: string, status?: string): Promise<SessionItem[]> {
  const params = new URLSearchParams()
  if (project) params.set('project', project)
  if (status) params.set('status', status)
  const query = params.toString() ? `?${params.toString()}` : ''
  const res = await fetch(`${API_BASE}/sessions${query}`)
  if (!res.ok) {
    throw new Error(`Failed to fetch sessions: HTTP ${res.status}`)
  }
  return res.json()
}

export async function createSession(payload: CreateSessionPayload): Promise<SessionItem> {
  const res = await fetch(`${API_BASE}/sessions`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) {
    throw new Error(`Failed to create session: HTTP ${res.status}`)
  }
  return res.json()
}

export async function deleteSession(id: string): Promise<void> {
  const res = await fetch(`${API_BASE}/sessions/${id}`, {
    method: 'DELETE',
  })
  if (!res.ok) {
    throw new Error(`Failed to delete session: HTTP ${res.status}`)
  }
}

export async function fetchObservations(sessionId: string, type?: string): Promise<ObservationItem[]> {
  const params = new URLSearchParams()
  if (type) params.set('obs_type', type)
  const query = params.toString() ? `?${params.toString()}` : ''
  const res = await fetch(`${API_BASE}/sessions/${sessionId}/observations${query}`)
  if (!res.ok) {
    throw new Error(`Failed to fetch observations: HTTP ${res.status}`)
  }
  return res.json()
}

export async function createObservation(
  sessionId: string,
  payload: CreateObservationPayload
): Promise<ObservationItem> {
  const res = await fetch(`${API_BASE}/sessions/${sessionId}/observations`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
  if (!res.ok) {
    throw new Error(`Failed to create observation: HTTP ${res.status}`)
  }
  return res.json()
}

export async function searchObservations(query?: string, project?: string): Promise<ObservationItem[]> {
  const params = new URLSearchParams()
  if (query) params.set('q', query)
  if (project) params.set('project', project)
  const res = await fetch(`${API_BASE}/observations/search?${params.toString()}`)
  if (!res.ok) {
    throw new Error(`Failed to search observations: HTTP ${res.status}`)
  }
  return res.json()
}
