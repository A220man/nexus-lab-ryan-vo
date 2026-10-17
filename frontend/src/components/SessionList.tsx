import React, { useState } from 'react'
import { SessionItem, CreateSessionPayload } from '../api'

interface SessionListProps {
  sessions: SessionItem[]
  selectedSessionId: string | null
  onSelectSession: (session: SessionItem) => void
  onCreateSession: (payload: CreateSessionPayload) => Promise<void>
  onDeleteSession: (id: string) => Promise<void>
  loading: boolean
}

export const SessionList: React.FC<SessionListProps> = ({
  sessions,
  selectedSessionId,
  onSelectSession,
  onCreateSession,
  onDeleteSession,
  loading,
}) => {
  const [showCreate, setShowCreate] = useState(false)
  const [project, setProject] = useState('nexus-core')
  const [name, setName] = useState('')
  const [description, setDescription] = useState('')
  const [platform, setPlatform] = useState('claude-code')
  const [submitting, setSubmitting] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!name.trim()) return
    setSubmitting(true)
    try {
      await onCreateSession({
        project: project.trim(),
        name: name.trim(),
        description: description.trim() || undefined,
        platform_source: platform,
      })
      setName('')
      setDescription('')
      setShowCreate(false)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <section className="card sessions-section">
      <div className="section-header">
        <h2>Agent Sessions</h2>
        <button
          className="btn-primary"
          onClick={() => setShowCreate(!showCreate)}
          aria-label="New Session"
        >
          {showCreate ? 'Cancel' : '+ New Session'}
        </button>
      </div>

      {showCreate && (
        <form className="session-form" onSubmit={handleSubmit} data-testid="create-session-form">
          <div className="form-group">
            <label htmlFor="session-project">Project</label>
            <input
              id="session-project"
              type="text"
              value={project}
              onChange={(e) => setProject(e.target.value)}
              required
            />
          </div>
          <div className="form-group">
            <label htmlFor="session-name">Session Name</label>
            <input
              id="session-name"
              type="text"
              placeholder="e.g. Memory Pipeline Refactor"
              value={name}
              onChange={(e) => setName(e.target.value)}
              required
            />
          </div>
          <div className="form-group">
            <label htmlFor="session-desc">Description</label>
            <textarea
              id="session-desc"
              rows={2}
              placeholder="Context or objectives for this session"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
            />
          </div>
          <div className="form-group">
            <label htmlFor="session-platform">Platform Source</label>
            <select
              id="session-platform"
              value={platform}
              onChange={(e) => setPlatform(e.target.value)}
            >
              <option value="claude-code">Claude Code</option>
              <option value="codex">Codex</option>
              <option value="opencode">OpenCode</option>
              <option value="custom">Custom Agent</option>
            </select>
          </div>
          <button type="submit" className="btn-success" disabled={submitting}>
            {submitting ? 'Creating...' : 'Create Session'}
          </button>
        </form>
      )}

      {loading ? (
        <p className="loading">Loading sessions...</p>
      ) : sessions.length === 0 ? (
        <p className="empty-state">No agent sessions recorded yet. Create one to begin tracking context.</p>
      ) : (
        <ul className="session-items">
          {sessions.map((s) => (
            <li
              key={s.id}
              className={`session-item ${selectedSessionId === s.id ? 'active' : ''}`}
              onClick={() => onSelectSession(s)}
            >
              <div className="session-item-header">
                <span className="session-name">{s.name}</span>
                <span className={`status-badge status-${s.status}`}>{s.status}</span>
              </div>
              <div className="session-item-meta">
                <span className="project-tag">{s.project}</span>
                {s.platform_source && <span className="platform-tag">{s.platform_source}</span>}
                <button
                  className="btn-delete"
                  title="Delete Session"
                  onClick={(e) => {
                    e.stopPropagation()
                    onDeleteSession(s.id)
                  }}
                  aria-label={`Delete ${s.name}`}
                >
                  &times;
                </button>
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
