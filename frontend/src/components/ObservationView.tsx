import React, { useState } from 'react'
import { SessionItem, ObservationItem, CreateObservationPayload } from '../api'

interface ObservationViewProps {
  session: SessionItem
  observations: ObservationItem[]
  onCreateObservation: (payload: CreateObservationPayload) => Promise<void>
  onSearch: (query: string) => Promise<void>
  loading: boolean
}

export const ObservationView: React.FC<ObservationViewProps> = ({
  session,
  observations,
  onCreateObservation,
  onSearch,
  loading,
}) => {
  const [showForm, setShowForm] = useState(false)
  const [title, setTitle] = useState('')
  const [type, setType] = useState<ObservationItem['type']>('feature')
  const [narrative, setNarrative] = useState('')
  const [filesEdited, setFilesEdited] = useState('')
  const [searchQuery, setSearchQuery] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    if (!title.trim()) return
    setSubmitting(true)
    try {
      const edited = filesEdited
        .split(',')
        .map((f) => f.trim())
        .filter(Boolean)
      await onCreateObservation({
        title: title.trim(),
        type,
        narrative: narrative.trim() || undefined,
        files_edited: edited.length ? edited : undefined,
      })
      setTitle('')
      setNarrative('')
      setFilesEdited('')
      setShowForm(false)
    } finally {
      setSubmitting(false)
    }
  }

  const handleSearchSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    onSearch(searchQuery.trim())
  }

  return (
    <section className="card observations-section">
      <div className="section-header">
        <div>
          <h2>Observations: {session.name}</h2>
          <p className="session-subtitle">
            Project: <strong>{session.project}</strong> | Status: <strong>{session.status}</strong>
          </p>
        </div>
        <button
          className="btn-primary"
          onClick={() => setShowForm(!showForm)}
          aria-label="Record Observation"
        >
          {showForm ? 'Cancel' : '+ Record Observation'}
        </button>
      </div>

      <form className="search-bar" onSubmit={handleSearchSubmit}>
        <input
          type="text"
          placeholder="Search observations by keyword or title..."
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          aria-label="Search observations"
        />
        <button type="submit" className="btn-secondary">
          Search
        </button>
        {searchQuery && (
          <button
            type="button"
            className="btn-link"
            onClick={() => {
              setSearchQuery('')
              onSearch('')
            }}
          >
            Clear
          </button>
        )}
      </form>

      {showForm && (
        <form className="observation-form" onSubmit={handleSubmit} data-testid="observation-form">
          <div className="form-group">
            <label htmlFor="obs-title">Observation Title</label>
            <input
              id="obs-title"
              type="text"
              placeholder="e.g. Enforced foreign key cascade on sessions"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              required
            />
          </div>
          <div className="form-group">
            <label htmlFor="obs-type">Classification Type</label>
            <select
              id="obs-type"
              value={type}
              onChange={(e) => setType(e.target.value as ObservationItem['type'])}
            >
              <option value="feature">Feature</option>
              <option value="bugfix">Bugfix</option>
              <option value="refactor">Refactor</option>
              <option value="verification">Verification</option>
              <option value="investigation">Investigation</option>
              <option value="neutral">Neutral</option>
            </select>
          </div>
          <div className="form-group">
            <label htmlFor="obs-narrative">Narrative / Summary</label>
            <textarea
              id="obs-narrative"
              rows={3}
              placeholder="Detailed description of what the agent learned or modified"
              value={narrative}
              onChange={(e) => setNarrative(e.target.value)}
            />
          </div>
          <div className="form-group">
            <label htmlFor="obs-files">Files Edited (comma-separated)</label>
            <input
              id="obs-files"
              type="text"
              placeholder="e.g. backend/app/main.py, backend/models/session.py"
              value={filesEdited}
              onChange={(e) => setFilesEdited(e.target.value)}
            />
          </div>
          <button type="submit" className="btn-success" disabled={submitting}>
            {submitting ? 'Recording...' : 'Save Observation'}
          </button>
        </form>
      )}

      {loading ? (
        <p className="loading">Loading observations...</p>
      ) : observations.length === 0 ? (
        <p className="empty-state">No observations recorded for this session yet.</p>
      ) : (
        <ul className="observation-items">
          {observations.map((obs) => (
            <li key={obs.id} className="observation-item">
              <div className="observation-item-header">
                <span className="observation-title">{obs.title}</span>
                <span className={`type-badge type-${obs.type}`}>{obs.type}</span>
              </div>
              {obs.narrative && <p className="observation-narrative">{obs.narrative}</p>}
              {obs.files_edited && obs.files_edited.length > 0 && (
                <div className="observation-files">
                  <span className="files-label">Edited:</span>
                  {obs.files_edited.map((file, idx) => (
                    <code key={idx} className="file-chip">
                      {file}
                    </code>
                  ))}
                </div>
              )}
              <div className="observation-footer">
                <span className="hash-label">Hash: {obs.content_hash.slice(0, 8)}...</span>
                {obs.occurrence_count > 1 && (
                  <span className="count-badge">x{obs.occurrence_count} observed</span>
                )}
              </div>
            </li>
          ))}
        </ul>
      )}
    </section>
  )
}
