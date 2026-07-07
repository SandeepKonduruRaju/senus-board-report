import React from 'react'

export function fmtEUR(v, opts = {}) {
  if (v === null || v === undefined) return '—'
  const abs = Math.abs(v)
  const sign = v < 0 ? '−' : ''
  return `${sign}€${abs.toLocaleString('en-IE', { maximumFractionDigits: opts.decimals ?? 0 })}`
}

export function fmtPct(v, decimals = 1) {
  if (v === null || v === undefined) return '—'
  return `${v.toFixed(decimals)}%`
}

export function KpiCard({ label, value, delta, deltaLabel, note, tone }) {
  const valueClass = tone === 'negative' ? 'negative' : tone === 'positive' ? 'positive' : ''
  const deltaClass = delta > 0 ? 'up' : delta < 0 ? 'down' : 'neutral'
  return (
    <div className="kpi-card">
      <div className="kpi-label">{label}</div>
      <div className={`kpi-value ${valueClass}`}>{value}</div>
      {deltaLabel && <div className={`kpi-delta ${deltaClass}`}>{deltaLabel}</div>}
      {note && <div className="kpi-note">{note}</div>}
    </div>
  )
}

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
  return <div className="disclosure"><b>Disclosure note —</b> {children}</div>
}

export const CHART_COLORS = {
  moss: '#7FA07A',
  clay: '#C08148',
  positive: '#7FB88F',
  negative: '#C97A5C',
  grid: '#2B3532',
  text: '#8B958E',
}
