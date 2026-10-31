import { useState } from 'react'
import { authService } from '../auth'

interface UserMenuProps {
  user: {
    name: string | null
    email: string | null
    roles: string[]
  }
  onLogout: () => void
}

export function UserMenu({ user, onLogout }: UserMenuProps) {
  const [open, setOpen] = useState(false)

  return (
    <div className="user-menu">
      <button
        className="user-menu-trigger"
        onClick={() => setOpen(!open)}
        aria-expanded={open}
        aria-haspopup="true"
      >
        <span className="user-avatar">
          {user.name?.[0]?.toUpperCase() || user.email?.[0]?.toUpperCase() || 'U'}
        </span>
        <span className="user-name">{user.name || user.email || 'User'}</span>
        <span className="user-menu-arrow" />
      </button>

      {open && (
        <div className="user-menu-dropdown">
          <div className="user-menu-header">
            <span className="user-menu-name">{user.name || 'User'}</span>
            <span className="user-menu-email">{user.email}</span>
          </div>
          <div className="user-menu-roles">
            {user.roles.map((role) => (
              <span key={role} className="role-badge">
                {role}
              </span>
            ))}
          </div>
          <hr />
          <button className="user-menu-item" onClick={onLogout}>
            <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2">
              <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
              <polyline points="16 17 21 12 16 7" />
              <line x1="21" y1="12" x2="9" y2="12" />
            </svg>
            Sign out
          </button>
        </div>
      )}
    </div>
  )
}
