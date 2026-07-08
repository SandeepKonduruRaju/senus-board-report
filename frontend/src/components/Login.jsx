/**
 * Login.jsx
 *
 * Simple credential gate. Credentials are hardcoded for this assessment
 * (no real auth backend is required/in scope). In production this would
 * redirect to the organisation's identity provider (OAuth / SAML).
 *
 * Accepts:
 *   CEO     / senus2030
 *   Board   / senus2030
 *   Analyst / senus2030
 */
import React, { useState } from 'react'

const VALID_USERS = {
  'CEO': 'senus2030',
  'Board': 'senus2030',
  'Analyst': 'senus2030',
}

export default function Login({ onLogin }) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState(null)
  const [loading, setLoading] = useState(false)

  function handleSubmit(e) {
    e.preventDefault()
    setError(null)
    setLoading(true)

    // Simulate network latency so it feels like a real auth call
    setTimeout(() => {
      const valid = VALID_USERS[username] === password
      if (valid) {
        onLogin(username)
      } else {
        setError('Invalid credentials. Use CEO / senus2030 to sign in.')
        setLoading(false)
      }
    }, 600)
  }

  return (
    <div className="login-page">
      {/* Contour-line background same as topbar */}
      <svg className="login-contour" viewBox="0 0 1200 800" preserveAspectRatio="none">
        {Array.from({ length: 10 }).map((_, i) => (
          <path
            key={i}
            d={`M -50 ${200 + i * 60} C 200 ${80 + i * 60}, 500 ${320 + i * 60}, 800 ${120 + i * 60} S 1100 ${260 + i * 60}, 1300 ${160 + i * 60}`}
            fill="none"
            stroke="#7FA07A"
            strokeWidth="1"
            opacity={0.4 - i * 0.03}
          />
        ))}
      </svg>

      <div className="login-card">
        <div className="login-brand">
          <div className="login-wordmark">Senus</div>
          <div className="login-tagline">Board Report Platform</div>
        </div>

        <form className="login-form" onSubmit={handleSubmit}>
          <div className="login-field">
            <label className="login-label">Username</label>
            <input
              className="login-input"
              type="text"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              placeholder="CEO"
              autoComplete="username"
              required
            />
          </div>

          <div className="login-field">
            <label className="login-label">Password</label>
            <input
              className="login-input"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              placeholder="••••••••"
              autoComplete="current-password"
              required
            />
          </div>

          {error && <div className="login-error">{error}</div>}

          <button className="login-btn" type="submit" disabled={loading}>
            {loading ? 'Signing in…' : 'Sign in'}
          </button>
        </form>

        <p className="login-footer">
          Senus PLC · Euronext Access+ Dublin · SENUS
        </p>
      </div>
    </div>
  )
}
