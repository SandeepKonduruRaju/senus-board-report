/**
 * Sections.jsx — all board report section components.
 *
 * Each export corresponds to one sidebar nav item.
 * Props shared via sectionProps from App.jsx:
 *   company, annual, f24, f25, h1, kpis, runway, targets
 */
import React, { useEffect, useState } from 'react'
import {
  ResponsiveContainer, BarChart, Bar, LineChart, Line, AreaChart, Area,
  PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
} from 'recharts'
import { api } from '../api'
import {
  fmtEUR, fmtPct, KpiCard, Panel, SectionHeading,
  DisclosureBanner, CHART_COLORS as C,
} from './ui.jsx'

// ---------------------------------------------------------------------------
// Shared constants
// ---------------------------------------------------------------------------

const SOURCE = 'Senus PLC Information Document, Dec 2025, Section 7.1'
const SOURCE_H1 = 'Senus PLC H1 FY2026 Interim Results, Mar 2026 (Assiduous investor portal)'

const TOOLTIP_STYLE = {
  background: '#1B2220',
  border: '1px solid #2B3532',
  borderRadius: 8,
  fontFamily: 'IBM Plex Mono',
  fontSize: 12,
  color: '#EDEFEA',
}

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function findKpi(kpis, label) {
  return kpis.find((k) => k.label === label)
}

function DeltaLabel({ value, suffix = '' }) {
  if (value === null || value === undefined) return null
  const up = value > 0
  return `${up ? '↑' : '↓'} ${fmtPct(Math.abs(value))}${suffix}`
}

// ---------------------------------------------------------------------------
// SECTION 00 — Overview
// ---------------------------------------------------------------------------

export function Overview({ f24, f25, h1, kpis, runway, targets }) {
  const rev    = findKpi(kpis, 'Revenue')
  const margin = findKpi(kpis, 'Gross Margin')
  const loss   = findKpi(kpis, 'Net Loss After Tax')
  const cash   = findKpi(kpis, 'Cash & Cash Equivalents')

  const trendData = [
    { year: 'FY2024', revenue: f24.turnover, grossProfit: f24.gross_profit },
    { year: 'FY2025', revenue: f25.turnover, grossProfit: f25.gross_profit },
    ...(h1?.turnover ? [{ year: 'H1 FY2026', revenue: h1.turnover, grossProfit: h1.gross_profit }] : []),
  ]

  const channelData = [
    { name: 'Enterprise', value: f25.revenue_channel_enterprise_pct },
    { name: 'R&D',        value: f25.revenue_channel_rd_pct },
    { name: 'Independent', value: f25.revenue_channel_independent_pct },
  ]

  return (
    <>
      <SectionHeading eyebrow="Board Report · FY2025" title="Company Overview" />
      <DisclosureBanner>
        All figures are drawn from Senus PLC's audited FY2024/FY2025 financials
        (Information Document, Dec 2025). Where a standard metric (EBITDA, Current
        Ratio, DSCR) cannot be reliably derived from what the Company has disclosed,
        it is <b>omitted or flagged</b> — never estimated.{' '}
        {h1 && h1.turnover != null && (
          <> H1 FY2026 (6 months to 31 Dec 2025) is included below — <b>unaudited</b>,
          published 19 Mar 2026.</>
        )}
      </DisclosureBanner>

      <div className="kpi-grid">
        <KpiCard
          label="Revenue (FY2025)"
          value={fmtEUR(rev.fy2025)}
          delta={rev.yoy_change_pct}
          deltaLabel={`↑ ${fmtPct(rev.yoy_change_pct)} YoY`}
          source={SOURCE}
        />
        <KpiCard
          label="Gross Margin"
          value={fmtPct(margin.fy2025)}
          delta={margin.yoy_change_pct}
          deltaLabel={`↑ ${margin.yoy_change_pct?.toFixed(1)}pp YoY`}
          source={SOURCE}
        />
        <KpiCard
          label="Net Loss After Tax"
          value={fmtEUR(loss.fy2025)}
          tone="negative"
          deltaLabel={`↓ ${fmtPct(Math.abs(loss.yoy_change_pct))} narrower than FY2024`}
          source={SOURCE}
        />
        <KpiCard
          label="Cash (period end)"
          value={fmtEUR(cash.fy2025)}
          tone="negative"
          deltaLabel={`↓ ${fmtPct(Math.abs(cash.yoy_change_pct))} YoY`}
          note="Dec-2025 placement (€1.1m gross) is post-period."
          source={SOURCE}
        />
      </div>

      <div className="panel-grid-2">
        <Panel title="Revenue & Gross Profit" sub="FY2024 vs FY2025, EUR">
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={trendData}>
              <CartesianGrid strokeDasharray="3 3" stroke={C.grid} vertical={false} />
              <XAxis dataKey="year" stroke={C.text} fontSize={12} fontFamily="IBM Plex Mono" />
              <YAxis stroke={C.text} fontSize={11} fontFamily="IBM Plex Mono"
                tickFormatter={(v) => `€${(v / 1000).toFixed(0)}k`} />
              <Tooltip contentStyle={TOOLTIP_STYLE} formatter={(v) => fmtEUR(v)} />
              <Legend wrapperStyle={{ fontSize: 12, fontFamily: 'IBM Plex Sans' }} />
              <Bar dataKey="revenue" name="Revenue" fill={C.moss} radius={[4, 4, 0, 0]} />
              <Bar dataKey="grossProfit" name="Gross Profit" fill={C.clay} radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </Panel>

        <Panel title="FY2025 Revenue by Channel" sub="Enterprise / R&D / Independent">
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie data={channelData} dataKey="value" nameKey="name"
                innerRadius={50} outerRadius={80} paddingAngle={2}>
                {channelData.map((_, i) => (
                  <Cell key={i} fill={[C.moss, C.clay, '#5C6663'][i]} />
                ))}
              </Pie>
              <Tooltip contentStyle={TOOLTIP_STYLE} formatter={(v) => `${v}%`} />
              <Legend wrapperStyle={{ fontSize: 12, fontFamily: 'IBM Plex Sans' }} />
            </PieChart>
          </ResponsiveContainer>
        </Panel>
      </div>

      <Panel title="Senus 2030 — Strategic Scorecard" sub="Board-stated targets vs current position">
        <table className="data-table">
          <thead>
            <tr>
              <th style={{ textAlign: 'left' }}>Target</th>
              <th>Current (FY2025)</th>
              <th>Senus 2030 Goal</th>
            </tr>
          </thead>
          <tbody>
            <tr>
              <td>Revenue CAGR</td>
              <td>21.6% (FY24→FY25)</td>
              <td>≥ {targets.revenue_cagr_target_pct}% p.a. to FY2030</td>
            </tr>
            <tr>
              <td>Enterprise customers</td>
              <td>{f25.customers_enterprise}</td>
              <td>{targets.enterprise_customers_target}+ by FY2030</td>
            </tr>
            <tr>
              <td>Avg Enterprise ACV</td>
              <td>€{f25.acv_enterprise_era?.toLocaleString()} (ERA, highest)</td>
              <td>&gt; €{targets.avg_acv_target_eur?.toLocaleString()} by FY2030</td>
            </tr>
            <tr>
              <td>Revenue outside Ireland</td>
              <td>{f25.revenue_international_pct}%</td>
              <td>&gt; {targets.non_ireland_revenue_target_pct}% by FY2030</td>
            </tr>
            <tr>
              <td>EBITDA</td>
              <td className="negative">
                Not yet positive (Op. loss €{Math.abs(f25.operating_profit_loss).toLocaleString()})
              </td>
              <td>Positive by {targets.ebitda_positive_target_year}</td>
            </tr>
          </tbody>
        </table>
      </Panel>
    </>
  )
}

// ---------------------------------------------------------------------------
// SECTION 01 — Growth & Revenue
// ---------------------------------------------------------------------------

export function GrowthRevenue({ f24, f25, h1, targets }) {
  const cagr = targets.revenue_cagr_target_pct / 100
  const projectionData = Array.from({ length: 6 }).reduce((acc, _, i) => {
    const prev = acc[acc.length - 1]
    acc.push({ year: `FY${2025 + i}`, target: Math.round(prev.target * (1 + cagr)) })
    return acc
  }, [{ year: 'FY2025', target: f25.turnover }])

  const geoData = [
    { year: 'FY2024', Ireland: f24.revenue_ireland_pct, International: f24.revenue_international_pct },
    { year: 'FY2025', Ireland: f25.revenue_ireland_pct, International: f25.revenue_international_pct },
  ]

  const acvData = [
    { product: 'Senus SOIL',    acv: f25.acv_enterprise_soil },
    { product: 'Senus TERRAIN', acv: f25.acv_enterprise_terrain },
    { product: 'Senus ERA',     acv: f25.acv_enterprise_era },
  ]

  const customerMix = [
    { name: 'Enterprise',  value: f25.customers_enterprise },
    { name: 'Independent', value: f25.customers_independent },
    { name: 'R&D',         value: f25.customers_rd },
  ]

  return (
    <>
      <SectionHeading eyebrow="Section 01" title="Growth & Revenue" />

      <div className="kpi-grid">
        <KpiCard label="FY2025 Revenue" value={fmtEUR(f25.turnover)}
          deltaLabel="↑ 21.6% YoY" source={SOURCE} />
        {h1?.turnover != null && (
          <KpiCard
            label="H1 FY2026 Revenue"
            value={fmtEUR(h1.turnover)}
            deltaLabel="↑ 4.1% vs H1 FY2025 (unaudited)"
            note="Slower H1 growth vs FY2025's 21.6% full-year — wet-weather delay to soil sampling season cited by the Board"
            source={SOURCE_H1}
          />
        )}
        <KpiCard label="Total Customers (FY2025)" value={f25.customers_total}
          note={`${f25.customers_enterprise} Enterprise · ${f25.customers_independent} Independent · ${f25.customers_rd} R&D`}
          source={SOURCE} />
        <KpiCard label="Revenue outside Ireland" value={fmtPct(f25.revenue_international_pct)}
          deltaLabel="↑ from 5% in FY2024" source={SOURCE} />
      </div>

      <div className="panel-grid-2">
        <Panel
          title="Revenue vs Senus 2030 Target Trajectory"
          sub="50% CAGR target path from FY2025 base — target model, not a forecast"
        >
          <ResponsiveContainer width="100%" height={230}>
            <LineChart data={projectionData}>
              <CartesianGrid strokeDasharray="3 3" stroke={C.grid} vertical={false} />
              <XAxis dataKey="year" stroke={C.text} fontSize={11} fontFamily="IBM Plex Mono" />
              <YAxis stroke={C.text} fontSize={11} fontFamily="IBM Plex Mono"
                tickFormatter={(v) => `€${(v / 1e6).toFixed(1)}m`} />
              <Tooltip contentStyle={TOOLTIP_STYLE} formatter={(v) => fmtEUR(v)} />
              <Line type="monotone" dataKey="target" name="50% CAGR target"
                stroke={C.clay} strokeDasharray="5 4" strokeWidth={2} dot={{ r: 3 }} />
            </LineChart>
          </ResponsiveContainer>
        </Panel>

        <Panel title="Geographic Revenue Mix" sub="% of revenue, Ireland vs International">
          <ResponsiveContainer width="100%" height={230}>
            <BarChart data={geoData} stackOffset="expand">
              <CartesianGrid strokeDasharray="3 3" stroke={C.grid} vertical={false} />
              <XAxis dataKey="year" stroke={C.text} fontSize={12} fontFamily="IBM Plex Mono" />
              <YAxis stroke={C.text} fontSize={11} fontFamily="IBM Plex Mono"
                tickFormatter={(v) => `${Math.round(v * 100)}%`} />
              <Tooltip contentStyle={TOOLTIP_STYLE} formatter={(v) => `${v}%`} />
              <Legend wrapperStyle={{ fontSize: 12, fontFamily: 'IBM Plex Sans' }} />
              <Bar dataKey="Ireland" stackId="a" fill={C.moss} />
              <Bar dataKey="International" stackId="a" fill={C.clay} />
            </BarChart>
          </ResponsiveContainer>
        </Panel>
      </div>

      <div className="panel-grid-2">
        <Panel title="Average ACV by Product (Enterprise)" sub="FY2025, EUR">
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={acvData} layout="vertical" margin={{ left: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={C.grid} horizontal={false} />
              <XAxis type="number" stroke={C.text} fontSize={11} fontFamily="IBM Plex Mono"
                tickFormatter={(v) => `€${v / 1000}k`} />
              <YAxis type="category" dataKey="product" stroke={C.text} fontSize={12} width={110} />
              <Tooltip contentStyle={TOOLTIP_STYLE} formatter={(v) => fmtEUR(v)} />
              <Bar dataKey="acv" fill={C.moss} radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </Panel>

        <Panel title="Customer Base by Channel" sub="FY2025, 138 total accounts">
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie data={customerMix} dataKey="value" nameKey="name"
                innerRadius={50} outerRadius={80} paddingAngle={2}>
                {customerMix.map((_, i) => (
                  <Cell key={i} fill={[C.moss, '#5C6663', C.clay][i]} />
                ))}
              </Pie>
              <Tooltip contentStyle={TOOLTIP_STYLE} />
              <Legend wrapperStyle={{ fontSize: 12, fontFamily: 'IBM Plex Sans' }} />
            </PieChart>
          </ResponsiveContainer>
        </Panel>
      </div>

      {h1?.pipeline_value_closed_in_period_eur != null && (
        <Panel title="Bookings & Pipeline (H1 FY2026)" sub="Disclosed in Half Year Results narrative, 19 Mar 2026">
          <div className="kpi-grid" style={{ marginBottom: 0 }}>
            <KpiCard
              label="Enterprise deals closed in period"
              value={h1.enterprise_customers_closed_in_period}
              note="New enterprise customer wins, H1 FY2026"
              source={SOURCE_H1}
            />
            <KpiCard
              label="Closed pipeline value"
              value={fmtEUR(h1.pipeline_value_closed_in_period_eur)}
              note="Across the 21 enterprise deals closed in H1 FY2026"
              source={SOURCE_H1}
            />
            <KpiCard
              label="Open pipeline value"
              value={fmtEUR(h1.pipeline_value_open_eur)}
              note="Further pipeline not yet closed, disclosed at period end"
              source={SOURCE_H1}
            />
          </div>
          <p className="kpi-note" style={{ marginTop: 14 }}>
            Named commercial wins in the period include a whole supply chain project with
            First Milk (UK), a doubled Bank of Ireland contract for phase 2, and a
            multi-annual €300k Department of Agriculture Biochar research contract with
            University of Limerick.
          </p>
        </Panel>
      )}
    </>
  )
}

// ---------------------------------------------------------------------------
// SECTION 02 — Profitability
// ---------------------------------------------------------------------------

export function Profitability({ f24, f25 }) {
  const marginData = [
    {
      year: 'FY2024',
      grossMarginPct: f24.gross_margin_pct,
      opLossPct: (f24.operating_profit_loss / f24.turnover) * 100,
    },
    {
      year: 'FY2025',
      grossMarginPct: f25.gross_margin_pct,
      opLossPct: (f25.operating_profit_loss / f25.turnover) * 100,
    },
  ]

  const costData = [
    { year: 'FY2024', costOfSales: f24.cost_of_sales, adminExpenses: f24.admin_expenses },
    { year: 'FY2025', costOfSales: f25.cost_of_sales, adminExpenses: f25.admin_expenses },
  ]

  return (
    <>
      <SectionHeading eyebrow="Section 02" title="Profitability" />
      <DisclosureBanner>
        EBITDA is <b>not separately disclosed</b> — D&A is not broken out from
        administrative expenses in Senus's summarised financials. Operating Loss is
        shown as the closest disclosed proxy.
      </DisclosureBanner>

      <div className="kpi-grid">
        <KpiCard label="Gross Margin" value={fmtPct(f25.gross_margin_pct)}
          deltaLabel="↑ 14.7pp YoY" source={SOURCE} />
        <KpiCard
          label="Operating Margin"
          value={fmtPct((f25.operating_profit_loss / f25.turnover) * 100)}
          tone="negative"
          deltaLabel="↑ from −164.3% in FY2024"
          note="Operating loss / revenue — EBITDA not computable"
          source={SOURCE}
        />
        <KpiCard label="R&D Intensity" value={fmtPct(f25.rd_expense_pct_revenue)}
          deltaLabel="↓ from 22.0% in FY2024" source={SOURCE} />
        <KpiCard label="Admin Expenses" value={fmtEUR(f25.admin_expenses)}
          deltaLabel="↓ 17.6% YoY" source={SOURCE} />
      </div>

      <div className="panel-grid-2">
        <Panel title="Margin Trend" sub="Gross Margin % vs Operating Margin %">
          <ResponsiveContainer width="100%" height={230}>
            <LineChart data={marginData}>
              <CartesianGrid strokeDasharray="3 3" stroke={C.grid} vertical={false} />
              <XAxis dataKey="year" stroke={C.text} fontSize={12} fontFamily="IBM Plex Mono" />
              <YAxis stroke={C.text} fontSize={11} fontFamily="IBM Plex Mono"
                tickFormatter={(v) => `${v.toFixed(0)}%`} />
              <Tooltip contentStyle={TOOLTIP_STYLE} formatter={(v) => `${v.toFixed(1)}%`} />
              <Legend wrapperStyle={{ fontSize: 12, fontFamily: 'IBM Plex Sans' }} />
              <Line type="monotone" dataKey="grossMarginPct" name="Gross Margin %"
                stroke={C.moss} strokeWidth={2} dot={{ r: 4 }} />
              <Line type="monotone" dataKey="opLossPct" name="Operating Margin %"
                stroke={C.clay} strokeWidth={2} dot={{ r: 4 }} />
            </LineChart>
          </ResponsiveContainer>
        </Panel>

        <Panel title="Cost Structure" sub="Cost of Sales vs Admin Expenses, EUR">
          <ResponsiveContainer width="100%" height={230}>
            <BarChart data={costData}>
              <CartesianGrid strokeDasharray="3 3" stroke={C.grid} vertical={false} />
              <XAxis dataKey="year" stroke={C.text} fontSize={12} fontFamily="IBM Plex Mono" />
              <YAxis stroke={C.text} fontSize={11} fontFamily="IBM Plex Mono"
                tickFormatter={(v) => `€${(v / 1000).toFixed(0)}k`} />
              <Tooltip contentStyle={TOOLTIP_STYLE} formatter={(v) => fmtEUR(v)} />
              <Legend wrapperStyle={{ fontSize: 12, fontFamily: 'IBM Plex Sans' }} />
              <Bar dataKey="costOfSales" name="Cost of Sales" stackId="a" fill={C.clay} />
              <Bar dataKey="adminExpenses" name="Admin Expenses" stackId="a" fill={C.moss}
                radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </Panel>
      </div>

      <Panel title="P&L Summary" sub="FY2024 vs FY2025, EUR">
        <table className="data-table">
          <thead>
            <tr>
              <th style={{ textAlign: 'left' }}>Line item</th>
              <th>FY2024</th>
              <th>FY2025</th>
            </tr>
          </thead>
          <tbody>
            {[
              ['Turnover', f24.turnover, f25.turnover, false],
              ['Gross Profit', f24.gross_profit, f25.gross_profit, false],
              ['Admin Expenses', f24.admin_expenses, f25.admin_expenses, true],
              ['Operating Profit/(Loss)', f24.operating_profit_loss, f25.operating_profit_loss, true],
              ['Profit/(Loss) Before Tax', f24.profit_loss_before_tax, f25.profit_loss_before_tax, true],
              ['Profit/(Loss) After Tax', f24.profit_loss_after_tax, f25.profit_loss_after_tax, true],
            ].map(([label, v24, v25, neg]) => (
              <tr key={label}>
                <td>{label}</td>
                <td className={neg ? 'negative' : ''}>{fmtEUR(v24)}</td>
                <td className={neg ? 'negative' : ''}>{fmtEUR(v25)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </Panel>
    </>
  )
}

// ---------------------------------------------------------------------------
// SECTION 03 — Cash & Liquidity
// ---------------------------------------------------------------------------

export function CashLiquidity({ f24, f25, h1, kpis, runway }) {
  const runwayKpi = findKpi(kpis, 'Cash Runway (pre-placement)')
  const est = runway.illustrative_estimate
  const actual = runway.actual_h1_fy2026

  const cashTrend = [
    { point: 'FY2024 open', cash: f24.cash_beginning },
    { point: 'FY2024 close', cash: f24.cash_end },
    { point: 'FY2025 close', cash: f25.cash_end },
    ...(actual ? [{ point: 'H1 FY2026 close (actual)', cash: actual.cash_end }] : []),
  ]

  const bridgeData = [
    { year: 'FY2024', operating: f24.cash_flow_operating, investing: f24.cash_flow_investing, financing: f24.cash_flow_financing },
    { year: 'FY2025', operating: f25.cash_flow_operating, investing: f25.cash_flow_investing, financing: f25.cash_flow_financing },
    ...(h1 && h1.cash_flow_operating != null
      ? [{ year: 'H1 FY2026', operating: h1.cash_flow_operating, investing: h1.cash_flow_investing, financing: h1.cash_flow_financing }]
      : []),
  ]

  return (
    <>
      <SectionHeading eyebrow="Section 03" title="Cash & Liquidity" />

      <div className="kpi-grid">
        <KpiCard label="Cash at 30 June 2025" value={fmtEUR(f25.cash_end)}
          tone="negative" deltaLabel="↓ 67.0% YoY" source={SOURCE} />
        <KpiCard
          label="Cash at 31 Dec 2025 (H1 FY2026, actual)"
          value={actual ? fmtEUR(actual.cash_end) : '—'}
          tone="positive"
          note="Reported Half Year Results, 19 Mar 2026 (unaudited)"
          source={SOURCE_H1}
        />
        <KpiCard
          label="Book Runway at FY2025 (pre-placement)"
          value={`${runwayKpi?.fy2025} months`}
          tone="negative"
          note="FYE cash ÷ avg monthly burn — excluded the not-yet-received placement"
          source={SOURCE}
        />
        <KpiCard
          label="Actual Runway from H1 FY2026"
          value={actual ? `${actual.runway_months_from_period_end} months` : '—'}
          tone="positive"
          note="H1 cash ÷ H1 monthly burn (~€68k/mo, up from ~€31k/mo pre-Loamin)"
          source={SOURCE_H1}
        />
      </div>

      {actual && (
        <DisclosureBanner>
          Before H1 FY2026 results existed, an illustrative estimate (FY2025 cash + gross
          placement proceeds, FY2025 burn rate assumed) implied ~€{(est.estimated_cash / 1000).toFixed(0)}k
          cash and a {est.estimated_runway_months}-month runway. The <b>actual</b> reported
          H1 FY2026 cash position was €{(actual.cash_end / 1000).toFixed(0)}k — lower than the
          estimate, because operating burn came in well above the FY2025 rate (Loamin integration
          costs) and a €124,837 loan repayment wasn't in the original assumption. The runway
          conclusion (~11 months) ends up similar, but for different reasons than the estimate
          assumed — a useful reminder to the Board that illustrative estimates need revisiting
          against actuals, not treated as forecasts.
        </DisclosureBanner>
      )}

      <div className="panel-grid-2">
        <Panel title="Cash Position" sub="EUR — FY2024 through H1 FY2026 actual">
          <ResponsiveContainer width="100%" height={230}>
            <AreaChart data={cashTrend}>
              <CartesianGrid strokeDasharray="3 3" stroke={C.grid} vertical={false} />
              <XAxis dataKey="point" stroke={C.text} fontSize={10} fontFamily="IBM Plex Mono"
                interval={0} angle={-12} textAnchor="end" height={60} />
              <YAxis stroke={C.text} fontSize={11} fontFamily="IBM Plex Mono"
                tickFormatter={(v) => `€${(v / 1000).toFixed(0)}k`} />
              <Tooltip contentStyle={TOOLTIP_STYLE} formatter={(v) => fmtEUR(v)} />
              <Area type="monotone" dataKey="cash" stroke={C.moss}
                fill={C.moss} fillOpacity={0.18} strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </Panel>

        <Panel title="Cash Flow Bridge" sub="Operating / Investing / Financing, EUR">
          <ResponsiveContainer width="100%" height={230}>
            <BarChart data={bridgeData}>
              <CartesianGrid strokeDasharray="3 3" stroke={C.grid} vertical={false} />
              <XAxis dataKey="year" stroke={C.text} fontSize={12} fontFamily="IBM Plex Mono" />
              <YAxis stroke={C.text} fontSize={11} fontFamily="IBM Plex Mono"
                tickFormatter={(v) => `€${(v / 1000).toFixed(0)}k`} />
              <Tooltip contentStyle={TOOLTIP_STYLE} formatter={(v) => fmtEUR(v)} />
              <Legend wrapperStyle={{ fontSize: 12, fontFamily: 'IBM Plex Sans' }} />
              <Bar dataKey="operating" name="Operating" fill={C.negative} />
              <Bar dataKey="investing" name="Investing"  fill={C.clay} />
              <Bar dataKey="financing" name="Financing"  fill={C.moss} />
            </BarChart>
          </ResponsiveContainer>
        </Panel>
      </div>

      <Panel title="Working Capital Components"
        sub="FY2024 / FY2025 disclose only specific items; H1 FY2026 discloses full current assets/liabilities">
        <table className="data-table">
          <thead>
            <tr><th style={{ textAlign: 'left' }}>Item</th><th>FY2024</th><th>FY2025</th><th>H1 FY2026</th></tr>
          </thead>
          <tbody>
            <tr>
              <td>Trade Debtors</td>
              <td>{fmtEUR(f24.trade_debtors)}</td>
              <td>{fmtEUR(f25.trade_debtors)}</td>
              <td>{fmtEUR(h1?.trade_debtors)}</td>
            </tr>
            <tr>
              <td>Trade Creditors</td>
              <td>{fmtEUR(f24.trade_creditors)}</td>
              <td>{fmtEUR(f25.trade_creditors)}</td>
              <td>{fmtEUR(h1?.creditors_due_within_1yr)}</td>
            </tr>
            <tr>
              <td>Bank Debt (&gt;1yr)</td>
              <td>—</td>
              <td>{fmtEUR(f25.new_bank_loan_sbci)}</td>
              <td>{fmtEUR(h1?.new_bank_loan_sbci)}</td>
            </tr>
            <tr>
              <td>Contingent Consideration (Loamin)</td>
              <td>—</td>
              <td>—</td>
              <td>{fmtEUR(h1?.contingent_consideration_loamin)}</td>
            </tr>
          </tbody>
        </table>
        <p className="kpi-note" style={{ marginTop: 14 }}>
          FY2024/FY2025 disclose only specific balance sheet components, so a standard Current
          Ratio couldn't be computed for those periods — it was omitted rather than estimated.
          H1 FY2026 discloses full current assets (€923,339) and current liabilities
          (€387,105 + €850,000 contingent consideration), giving a Current Ratio of ~0.75×
          once the Loamin earn-out is included as a current liability — worth the Board's
          attention given it's below 1.0×, largely a function of the newly-recognised
          contingent consideration rather than a change in underlying trading liquidity.
        </p>
      </Panel>
    </>
  )
}

// ---------------------------------------------------------------------------
// SECTION 04 — Solvency & Leverage
// ---------------------------------------------------------------------------

export function SolvencyLeverage({ f24, f25 }) {
  const equityData = [
    { year: 'FY2024', netAssets: f24.net_assets_liabilities },
    { year: 'FY2025', netAssets: f25.net_assets_liabilities },
  ]

  return (
    <>
      <SectionHeading eyebrow="Section 04" title="Solvency & Leverage" />
      <DisclosureBanner>
        Interest expense and the SBCI loan amortisation schedule are not separately
        disclosed — a <b>Debt Service Coverage Ratio cannot be reliably computed</b>.
        Net finance cost and loan balance are shown instead.
      </DisclosureBanner>

      <div className="kpi-grid">
        <KpiCard
          label="Net Assets / (Liabilities)"
          value={fmtEUR(f25.net_assets_liabilities)}
          tone="negative"
          note="Turned negative in FY2025 from €574k net assets in FY2024"
          source={SOURCE}
        />
        <KpiCard label="Retained Earnings (deficit)" value={fmtEUR(f25.retained_earnings)}
          tone="negative" source={SOURCE} />
        <KpiCard label="SBCI Term Loan (FY2025)" value={fmtEUR(f25.new_bank_loan_sbci)}
          note="First institutional debt" source={SOURCE} />
        <KpiCard
          label="Net Finance Cost (FY2025)"
          value={fmtEUR(f25.profit_loss_before_tax - f25.operating_profit_loss)}
          note="PBT less Operating Loss — not separately itemised in source"
          source={SOURCE}
        />
      </div>

      <Panel title="Net Assets / (Liabilities) Trend"
        sub="EUR — balance sheet crossed into net liabilities in FY2025">
        <ResponsiveContainer width="100%" height={230}>
          <BarChart data={equityData}>
            <CartesianGrid strokeDasharray="3 3" stroke={C.grid} vertical={false} />
            <XAxis dataKey="year" stroke={C.text} fontSize={12} fontFamily="IBM Plex Mono" />
            <YAxis stroke={C.text} fontSize={11} fontFamily="IBM Plex Mono"
              tickFormatter={(v) => `€${(v / 1000).toFixed(0)}k`} />
            <Tooltip contentStyle={TOOLTIP_STYLE} formatter={(v) => fmtEUR(v)} />
            <Bar dataKey="netAssets" radius={[4, 4, 0, 0]}>
              {equityData.map((d, i) => (
                <Cell key={i} fill={d.netAssets >= 0 ? C.moss : C.negative} />
              ))}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </Panel>

      <Panel title="Why leverage metrics are limited at this stage">
        <p style={{ fontSize: 13.5, color: 'var(--text-muted)', lineHeight: 1.7, margin: 0 }}>
          Senus is pre-EBITDA-positive and funded primarily through private placements and
          director loans — the SBCI facility is its first meaningful institutional debt.
          Classic leverage ratios (Net Debt/EBITDA, DSCR, Interest Cover) either divide by
          a negative denominator or rely on figures not yet disclosed at that granularity.
          These metrics will become meaningful as Senus scales toward its stated FY2028
          EBITDA-positive target — the Board should request the underlying disclosures then.
        </p>
      </Panel>
    </>
  )
}

// ---------------------------------------------------------------------------
// SECTION 05 — Returns
// ---------------------------------------------------------------------------

export function Returns({ company, f24, f25 }) {
  return (
    <>
      <SectionHeading eyebrow="Section 05" title="Returns" />
      <DisclosureBanner>
        FY2025 closed with net liabilities of €(15,575) — capital employed is near zero
        or negative, so <b>ROCE is intentionally omitted</b> rather than shown as a
        large or misleading number.
      </DisclosureBanner>

      <div className="kpi-grid">
        <KpiCard label="Admission Share Price" value={`€${company.admission_share_price_eur}`}
          source="Euronext Access+ admission, 22 Dec 2025" />
        <KpiCard label="Market Cap at Listing" value={fmtEUR(company.market_cap_at_listing_eur)}
          source="Euronext Access+ admission, 22 Dec 2025" />
        <KpiCard label="Shares in Issue" value={company.shares_in_issue.toLocaleString()}
          source="Euronext Access+ admission, 22 Dec 2025" />
        <KpiCard label="ROCE (FY2025)" value="Not meaningful" tone="negative"
          note="Capital employed ≈ €0 / negative" source={SOURCE} />
      </div>

      <Panel title="Valuation context">
        <p style={{ fontSize: 13.5, color: 'var(--text-muted)', lineHeight: 1.7, margin: 0 }}>
          Senus listed at an implied valuation of €13.1m (post-money, Dec-2025 placement),
          against FY2025 revenue of {fmtEUR(f25.turnover)} — roughly a{' '}
          <b>15.7× revenue multiple</b>, consistent with early-stage vertical SaaS at 77%+
          gross margin but pre-profitability. Traditional return metrics (ROCE, ROE) will
          only become informative once the balance sheet returns to positive equity —
          which is itself a useful binary milestone for the Board to track.
        </p>
      </Panel>
    </>
  )
}

// ---------------------------------------------------------------------------
// SECTION 06 — AI Insights
// ---------------------------------------------------------------------------

export function AIInsights() {
  const [section, setSection] = useState('overview')
  const [data, setData]       = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    setData(null)
    api.insights(section)
      .then((d) => { setData(d); setLoading(false) })
      .catch(() => setLoading(false))
  }, [section])

  const sections = ['overview', 'growth', 'profitability', 'cash', 'solvency', 'returns']

  return (
    <>
      <SectionHeading eyebrow="Section 06" title="AI-Generated Board Commentary" />
      <DisclosureBanner>
        Commentary is generated from the same audited dataset shown throughout this report.
        The model is instructed to cite only figures present in the data and to name risks
        plainly. Treat as a first draft for the Board — not a substitute for management narrative.
      </DisclosureBanner>

      <div style={{ display: 'flex', gap: 8, marginBottom: 20, flexWrap: 'wrap' }}>
        {sections.map((s) => (
          <button
            key={s}
            className={`nav-item ${section === s ? 'active' : ''}`}
            style={{ display: 'inline-flex', width: 'auto' }}
            onClick={() => setSection(s)}
          >
            {s[0].toUpperCase() + s.slice(1)}
          </button>
        ))}
      </div>

      <Panel>
        {loading && <p style={{ color: 'var(--text-muted)' }}>Generating commentary…</p>}
        {!loading && !data && <p style={{ color: 'var(--negative)' }}>Failed to load — is the backend running?</p>}
        {!loading && data && (
          <>
            <div className="insight-box">{data.commentary}</div>
            <div className="insight-tag"><span className="dot" />{data.generated_by}</div>
          </>
        )}
      </Panel>
    </>
  )
}
