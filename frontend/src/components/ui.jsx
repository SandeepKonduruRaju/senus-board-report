/**
 * ui.jsx — shared primitives and formatting helpers.
 *
 * Kept deliberately thin: only things used by 2+ section components live here.
 */
import React from 'react'
import SourceTooltip from './SourceTooltip.jsx'

// ---------------------------------------------------------------------------
// Formatters
// ---------------------------------------------------------------------------

export function fmtEUR(v, { decimals = 0 } = {}) {
  if (v === null || v === undefined) return '—'
  const abs = Math.abs(v)
  const sign = v < 0 ? '−' : ''
  return `${sign}€${abs.toLocaleString('en-IE', { maximumFractionDigits: decimals })}`
}

export function fmtPct(v, decimals = 1) {
  if (v === null || v === undefined) return '—'
  return `${Number(v).toFixed(decimals)}%`
}

// ---------------------------------------------------------------------------
// KPI card
// ---------------------------------------------------------------------------

/**
 * @param {string}  label
 * @param {string}  value        — pre-formatted display value
 * @param {number}  [delta]      — raw numeric delta (determines arrow colour)
 * @param {string}  [deltaLabel] — human-readable delta string
 * @param {string}  [note]       — secondary disclosure note
 * @param {string}  [source]     — document source for tooltip
 * @param {'positive'|'negative'|null} [tone]
 */
export function KpiCard({ label, value, delta, deltaLabel, note, source, tone }) {
  const valueClass = tone === 'negative' ? 'negative' : tone === 'positive' ? 'positive' : ''
  const deltaClass = delta > 0 ? 'up' : delta < 0 ? 'down' : 'neutral'

  return (
    <div className="kpi-card">
      <div className="kpi-label">
        {label}
        <SourceTooltip source={source} />
      </div>
      <div className={`kpi-value ${valueClass}`}>{value}</div>
      {deltaLabel && <div className={`kpi-delta ${deltaClass}`}>{deltaLabel}</div>}
      {note && <div className="kpi-note">{note}</div>}
    </div>
  )
}

// ---------------------------------------------------------------------------
// Layout primitives
// ---------------------------------------------------------------------------

export function Panel({ title, sub, children }) {
  return (
    <div className="panel">
      {title && <p className="panel-title">{title}</p>}
      {sub && <p className="panel-sub">{sub}</p>}
      {children}
    </div>
  )
}

export function SectionHeading({ eyebrow, title }) {
  return (
    <>
      <div className="section-eyebrow">{eyebrow}</div>
      <h2 className="section-title">{title}</h2>
    </>
  )
}

export function DisclosureBanner({ children }) {
  return <div className="disclosure"><b>Disclosure note — </b>{children}</div>
}

export function H1PendingBadge() {
  return (
    <span className="h1-pending-badge" title="H1 FY2026 results published via Assiduous investor portal — not yet publicly accessible at build time">
      H1 FY2026 pending
    </span>
  )
}

// ---------------------------------------------------------------------------
// Design tokens (chart colours matching the CSS palette)
// ---------------------------------------------------------------------------

export const CHART_COLORS = {
  moss:     '#7FA07A',
  clay:     '#C08148',
  positive: '#7FB88F',
  negative: '#C97A5C',
  grid:     '#2B3532',
  text:     '#8B958E',
}
