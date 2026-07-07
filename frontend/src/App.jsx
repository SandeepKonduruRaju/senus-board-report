import React, { useEffect, useState } from 'react'
import { api } from './api'
import {
  Overview, GrowthRevenue, Profitability, CashLiquidity,
  SolvencyLeverage, Returns, AIInsights,
} from './components/Sections.jsx'

const SECTIONS = [
  { key: 'overview', label: 'Overview', idx: '00' },
  { key: 'growth', label: 'Growth & Revenue', idx: '01' },
  { key: 'profitability', label: 'Profitability', idx: '02' },
  { key: 'cash', label: 'Cash & Liquidity', idx: '03' },
  { key: 'solvency', label: 'Solvency & Leverage', idx: '04' },
  { key: 'returns', label: 'Returns', idx: '05' },
  { key: 'insights', label: 'AI Insights', idx: '06' },
]

function ContourBackground() {
  // Signature element: topographic contour lines, evoking Senus's own
  // land/habitat mapping work — the visual language of what the company does.
  const lines = Array.from({ length: 7 }).map((_, i) => {
    const offset = i * 26
    return (
      <path
        key={i}
        d={`M -50 ${140 + offset} C 150 ${60 + offset}, 350 ${220 + offset}, 550 ${100 + offset} S 950 ${180 + offset}, 1250 ${90 + offset}`}
        fill="none"
        stroke="#7FA07A"
        strokeWidth="1"
        opacity={0.5 - i * 0.06}
      />
    )
  })
  return (
    <svg className="contour-bg" viewBox="0 0 1200 300" preserveAspectRatio="none">
      {lines}
    </svg>
  )
}

export default function App() {
  const [active, setActive] = useState('overview')
  const [company, setCompany] = useState(null)
  const [annual, setAnnual] = useState(null)
  const [kpis, setKpis] = useState(null)
  const [runway, setRunway] = useState(null)
  const [targets, setTargets] = useState(null)
  const [error, setError] = useState(null)

  useEffect(() => {
    Promise.all([
      api.company(), api.annual(), api.kpis(), api.proFormaRunway(), api.strategyTargets(),
    ])
      .then(([c, a, k, r, t]) => {
        setCompany(c); setAnnual(a); setKpis(k); setRunway(r); setTargets(t)
      })
      .catch((e) => setError(e.message))
  }, [])

  if (error) {
    return (
      <div className="error">
        Could not reach the API ({error}).<br />
        Is the backend running? See README — <code>uvicorn app.main:app --reload</code>
      </div>
    )
  }
  if (!company || !annual || !kpis) {
    return <div className="loading">Loading board data…</div>
  }

  const f24 = annual.find((r) => r.fiscal_year === 'FY2024')
  const f25 = annual.find((r) => r.fiscal_year === 'FY2025')

  const sectionProps = { company, annual, f24, f25, kpis, runway, targets }

  const renderSection = () => {
    switch (active) {
      case 'growth': return <GrowthRevenue {...sectionProps} />
      case 'profitability': return <Profitability {...sectionProps} />
      case 'cash': return <CashLiquidity {...sectionProps} />
      case 'solvency': return <SolvencyLeverage {...sectionProps} />
      case 'returns': return <Returns {...sectionProps} />
      case 'insights': return <AIInsights {...sectionProps} />
      default: return <Overview {...sectionProps} />
    }
  }

  return (
    <div className="app">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-mark">Senus</div>
          <div className="brand-sub">Board Report</div>
        </div>
        <nav className="nav">
          {SECTIONS.map((s) => (
            <button
              key={s.key}
              className={`nav-item ${active === s.key ? 'active' : ''}`}
              onClick={() => setActive(s.key)}
            >
              <span className="nav-index">{s.idx}</span>
              {s.label}
            </button>
          ))}
        </nav>
        <div className="sidebar-footer">
          FY ends 30 June<br />
          Source: Information Document,<br />Dec 2025 Direct Listing
        </div>
      </aside>

      <main>
        <header className="topbar">
          <ContourBackground />
          <div className="topbar-content">
            <div>
              <h1 className="topbar-title">{company.name}</h1>
              <div className="topbar-meta">
                <span><b>{company.ticker}</b> · {company.exchange}</span>
                <span>ISIN <b>{company.isin}</b></span>
                <span>{company.employees} employees</span>
                <span>FY2025 revenue <b>€{f25.turnover.toLocaleString()}</b></span>
              </div>
            </div>
            <div className="ticker-pill">Admission price €{company.admission_share_price_eur}</div>
          </div>
        </header>
        <div className="content">{renderSection()}</div>
      </main>
    </div>
  )
}
