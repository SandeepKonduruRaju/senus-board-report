import React, { useEffect, useState } from 'react'
import {
  ResponsiveContainer, BarChart, Bar, LineChart, Line, AreaChart, Area,
  PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend,
} from 'recharts'
import { api } from '../api'
import { fmtEUR, fmtPct, KpiCard, Panel, SectionHeading, DisclosureBanner, CHART_COLORS as C } from './ui.jsx'

const tooltipStyle = {
  background: '#1B2220', border: '1px solid #2B3532', borderRadius: 8,
  fontFamily: 'IBM Plex Mono', fontSize: 12, color: '#EDEFEA',
}

function findKpi(kpis, label) {
  return kpis.find((k) => k.label === label)
}

/* ---------------------------- OVERVIEW ---------------------------- */
export function Overview({ f24, f25, kpis, runway, targets }) {
  const rev = findKpi(kpis, 'Revenue')
  const margin = findKpi(kpis, 'Gross Margin')
  const netLoss = findKpi(kpis, 'Net Loss After Tax')
  const cash = findKpi(kpis, 'Cash & Cash Equivalents (period end)')

  const trendData = [
    { year: 'FY2024', revenue: f24.turnover, grossProfit: f24.gross_profit },
    { year: 'FY2025', revenue: f25.turnover, grossProfit: f25.gross_profit },
  ]

  const channelData = [
    { name: 'Enterprise', value: f25.revenue_channel_enterprise_pct },
    { name: 'R&D', value: f25.revenue_channel_rd_pct },
    { name: 'Independent', value: f25.revenue_channel_independent_pct },
  ]
  const pieColors = [C.moss, C.clay, '#5C6663']

  return (
    <>
      <SectionHeading eyebrow="Board Report · FY2025" title="Company Overview" />
      <DisclosureBanner>
        All figures below are drawn from Senus PLC's audited FY2024/FY2025 financials as
        reported in the December 2025 Information Document. Where a standard metric (EBITDA,
        Current Ratio, DSCR) cannot be reliably derived from what the Company has disclosed,
        it is <b>omitted or flagged</b> rather than estimated — see each section for specifics.
      </DisclosureBanner>

      <div className="kpi-grid">
        <KpiCard label="Revenue (FY2025)" value={fmtEUR(rev.fy2025)} delta={rev.yoy_change_pct}
          deltaLabel={`${rev.yoy_change_pct > 0 ? '↑' : '↓'} ${fmtPct(rev.yoy_change_pct)} YoY`} />
        <KpiCard label="Gross Margin" value={fmtPct(margin.fy2025)} delta={margin.yoy_change_pct}
          deltaLabel={`${margin.yoy_change_pct > 0 ? '↑' : '↓'} ${margin.yoy_change_pct.toFixed(1)}pp YoY`} />
        <KpiCard label="Net Loss After Tax" value={fmtEUR(netLoss.fy2025)} tone="negative"
          deltaLabel={`↓ ${fmtPct(Math.abs(netLoss.yoy_change_pct))} narrower than FY2024`} />
        <KpiCard label="Cash at Period End" value={fmtEUR(cash.fy2025)} tone="negative"
          deltaLabel={`↓ ${fmtPct(Math.abs(cash.yoy_change_pct))} YoY`}
          note="Dec-2025 placement (€1.1m gross) is a post-period event, not in this balance." />
      </div>

      <div className="panel-grid-2">
        <Panel title="Revenue & Gross Profit" sub="FY2024 vs FY2025, EUR">
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={trendData}>
              <CartesianGrid strokeDasharray="3 3" stroke={C.grid} vertical={false} />
              <XAxis dataKey="year" stroke={C.text} fontSize={12} fontFamily="IBM Plex Mono" />
              <YAxis stroke={C.text} fontSize={11} fontFamily="IBM Plex Mono"
                tickFormatter={(v) => `€${(v / 1000).toFixed(0)}k`} />
              <Tooltip contentStyle={tooltipStyle} formatter={(v) => fmtEUR(v)} />
              <Legend wrapperStyle={{ fontSize: 12, fontFamily: 'IBM Plex Sans' }} />
              <Bar dataKey="revenue" name="Revenue" fill={C.moss} radius={[4, 4, 0, 0]} />
              <Bar dataKey="grossProfit" name="Gross Profit" fill={C.clay} radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </Panel>

        <Panel title="FY2025 Revenue by Channel" sub="Enterprise / R&D / Independent">
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie data={channelData} dataKey="value" nameKey="name" innerRadius={50} outerRadius={80}
                paddingAngle={2}>
                {channelData.map((_, i) => <Cell key={i} fill={pieColors[i]} />)}
              </Pie>
              <Tooltip contentStyle={tooltipStyle} formatter={(v) => `${v}%`} />
              <Legend wrapperStyle={{ fontSize: 12, fontFamily: 'IBM Plex Sans' }} />
            </PieChart>
          </ResponsiveContainer>
        </Panel>
      </div>

      <Panel title="Senus 2030 — Strategic Scorecard" sub="Board-stated targets vs current position">
        <table className="data-table">
          <thead>
            <tr><th style={{ textAlign: 'left' }}>Target</th><th>Current (FY2025)</th><th>Senus 2030 Goal</th></tr>
          </thead>
          <tbody>
            <tr><td>Revenue CAGR (from FY2025 base)</td><td>21.6% (FY24→FY25 actual)</td><td>≥ {targets.revenue_cagr_target_pct}% p.a. to FY2030</td></tr>
            <tr><td>Enterprise customers</td><td>{f25.customers_enterprise}</td><td>{targets.enterprise_customers_target}+ by FY2030</td></tr>
            <tr><td>Avg Enterprise ACV</td><td>€{f25.acv_enterprise_era.toLocaleString()} (ERA, highest tier)</td><td>&gt; €{targets.avg_acv_target_eur.toLocaleString()} by FY2030</td></tr>
            <tr><td>Revenue outside Ireland</td><td>{f25.revenue_international_pct}%</td><td>&gt; {targets.non_ireland_revenue_target_pct}% by FY2030</td></tr>
            <tr><td>EBITDA</td><td>Not yet positive (Op. loss €{Math.abs(f25.operating_profit_loss).toLocaleString()})</td><td>Positive by {targets.ebitda_positive_target_year}</td></tr>
          </tbody>
        </table>
      </Panel>
    </>
  )
}

/* ------------------------- GROWTH & REVENUE ------------------------- */
export function GrowthRevenue({ f24, f25, targets }) {
  const revYoY = [
    { year: 'FY2024', revenue: f24.turnover },
    { year: 'FY2025', revenue: f25.turnover },
  ]

  // Illustrative Senus 2030 trajectory at the Board's stated 50% CAGR floor.
  // Clearly a target model, not a forecast — labelled as such in the chart.
  const cagr = targets.revenue_cagr_target_pct / 100
  const projection = []
  let rev = f25.turnover
  const startYear = 2025
  for (let i = 0; i <= 5; i++) {
    projection.push({ year: `FY${startYear + i}`, target: Math.round(rev) })
    rev *= (1 + cagr)
  }

  const geoData = [
    { year: 'FY2024', Ireland: f24.revenue_ireland_pct, International: f24.revenue_international_pct },
    { year: 'FY2025', Ireland: f25.revenue_ireland_pct, International: f25.revenue_international_pct },
  ]

  const acvData = [
    { product: 'Senus SOIL', acv: f25.acv_enterprise_soil },
    { product: 'Senus TERRAIN', acv: f25.acv_enterprise_terrain },
    { product: 'Senus ERA', acv: f25.acv_enterprise_era },
  ]

  const customerMix = [
    { name: 'Enterprise', value: f25.customers_enterprise },
    { name: 'Independent', value: f25.customers_independent },
    { name: 'R&D', value: f25.customers_rd },
  ]
  const pieColors = [C.moss, '#5C6663', C.clay]

  return (
    <>
      <SectionHeading eyebrow="Section 01" title="Growth & Revenue" />

      <div className="kpi-grid">
        <KpiCard label="FY2025 Revenue" value={fmtEUR(f25.turnover)} deltaLabel="↑ 21.6% YoY" />
        <KpiCard label="Total Customer Accounts" value={f25.customers_total} note={`36 Enterprise · 98 Independent · 4 R&D`} />
        <KpiCard label="Revenue outside Ireland" value={fmtPct(f25.revenue_international_pct)}
          deltaLabel="↑ from 5% in FY2024" />
        <KpiCard label="Highest-tier Enterprise ACV" value={fmtEUR(f25.acv_enterprise_era)} note="Senus ERA — financial institution clients" />
      </div>

      <div className="panel-grid-2">
        <Panel title="Revenue vs Senus 2030 Target Trajectory" sub="EUR — target line assumes the Board's stated 50% CAGR floor from the FY2025 base; it is a target model, not a forecast">
          <ResponsiveContainer width="100%" height={230}>
            <LineChart data={projection}>
              <CartesianGrid strokeDasharray="3 3" stroke={C.grid} vertical={false} />
              <XAxis dataKey="year" stroke={C.text} fontSize={11} fontFamily="IBM Plex Mono" />
              <YAxis stroke={C.text} fontSize={11} fontFamily="IBM Plex Mono"
                tickFormatter={(v) => `€${(v / 1e6).toFixed(1)}m`} />
              <Tooltip contentStyle={tooltipStyle} formatter={(v) => fmtEUR(v)} />
              <Line type="monotone" dataKey="target" name="50% CAGR target path" stroke={C.clay}
                strokeDasharray="5 4" strokeWidth={2} dot={{ r: 3 }} />
            </LineChart>
          </ResponsiveContainer>
        </Panel>

        <Panel title="Geographic Mix" sub="% of revenue, Ireland vs International">
          <ResponsiveContainer width="100%" height={230}>
            <BarChart data={geoData} stackOffset="expand">
              <CartesianGrid strokeDasharray="3 3" stroke={C.grid} vertical={false} />
              <XAxis dataKey="year" stroke={C.text} fontSize={12} fontFamily="IBM Plex Mono" />
              <YAxis stroke={C.text} fontSize={11} fontFamily="IBM Plex Mono" tickFormatter={(v) => `${Math.round(v * 100)}%`} />
              <Tooltip contentStyle={tooltipStyle} formatter={(v) => `${v}%`} />
              <Legend wrapperStyle={{ fontSize: 12, fontFamily: 'IBM Plex Sans' }} />
              <Bar dataKey="Ireland" stackId="a" fill={C.moss} />
              <Bar dataKey="International" stackId="a" fill={C.clay} />
            </BarChart>
          </ResponsiveContainer>
        </Panel>
      </div>

      <div className="panel-grid-2">
        <Panel title="Average Annual Contract Value by Product" sub="FY2025, Enterprise customers, EUR">
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={acvData} layout="vertical" margin={{ left: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke={C.grid} horizontal={false} />
              <XAxis type="number" stroke={C.text} fontSize={11} fontFamily="IBM Plex Mono" tickFormatter={(v) => `€${(v / 1000)}k`} />
              <YAxis type="category" dataKey="product" stroke={C.text} fontSize={12} width={110} />
              <Tooltip contentStyle={tooltipStyle} formatter={(v) => fmtEUR(v)} />
              <Bar dataKey="acv" fill={C.moss} radius={[0, 4, 4, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </Panel>

        <Panel title="Customer Base by Channel" sub="FY2025, 138 total accounts">
          <ResponsiveContainer width="100%" height={220}>
            <PieChart>
              <Pie data={customerMix} dataKey="value" nameKey="name" innerRadius={50} outerRadius={80} paddingAngle={2}>
                {customerMix.map((_, i) => <Cell key={i} fill={pieColors[i]} />)}
              </Pie>
              <Tooltip contentStyle={tooltipStyle} />
              <Legend wrapperStyle={{ fontSize: 12, fontFamily: 'IBM Plex Sans' }} />
            </PieChart>
          </ResponsiveContainer>
        </Panel>
      </div>
    </>
  )
}

/* --------------------------- PROFITABILITY --------------------------- */
export function Profitability({ f24, f25 }) {
  const marginData = [
    { year: 'FY2024', grossMarginPct: f24.gross_margin_pct, opLossPct: (f24.operating_profit_loss / f24.turnover) * 100 },
    { year: 'FY2025', grossMarginPct: f25.gross_margin_pct, opLossPct: (f25.operating_profit_loss / f25.turnover) * 100 },
  ]

  const costData = [
    { year: 'FY2024', costOfSales: f24.cost_of_sales, adminExpenses: f24.admin_expenses },
    { year: 'FY2025', costOfSales: f25.cost_of_sales, adminExpenses: f25.admin_expenses },
  ]

  return (
    <>
      <SectionHeading eyebrow="Section 02" title="Profitability" />
      <DisclosureBanner>
        EBITDA is <b>not separately disclosed</b> — depreciation & amortisation is not broken
        out from administrative expenses in the summarised financials. Operating Loss is shown
        as the closest disclosed proxy rather than an invented EBITDA figure.
      </DisclosureBanner>

      <div className="kpi-grid">
        <KpiCard label="Gross Margin" value={fmtPct(f25.gross_margin_pct)} deltaLabel="↑ 14.7pp YoY" />
        <KpiCard label="Operating Margin" value={fmtPct((f25.operating_profit_loss / f25.turnover) * 100)}
          tone="negative" deltaLabel="↑ from −164.3% in FY2024" note="Operating loss / revenue" />
        <KpiCard label="R&D Intensity" value={fmtPct(f25.rd_expense_pct_revenue)} deltaLabel="↓ from 22.0% in FY2024"
          note="R&D expense as % of revenue" />
        <KpiCard label="Admin Expenses" value={fmtEUR(f25.admin_expenses)} deltaLabel="↓ 17.6% YoY" />
      </div>

      <div className="panel-grid-2">
        <Panel title="Margin Trend" sub="Gross Margin % vs Operating Margin %">
          <ResponsiveContainer width="100%" height={230}>
            <LineChart data={marginData}>
              <CartesianGrid strokeDasharray="3 3" stroke={C.grid} vertical={false} />
              <XAxis dataKey="year" stroke={C.text} fontSize={12} fontFamily="IBM Plex Mono" />
              <YAxis stroke={C.text} fontSize={11} fontFamily="IBM Plex Mono" tickFormatter={(v) => `${v}%`} />
              <Tooltip contentStyle={tooltipStyle} formatter={(v) => `${v.toFixed(1)}%`} />
              <Legend wrapperStyle={{ fontSize: 12, fontFamily: 'IBM Plex Sans' }} />
              <Line type="monotone" dataKey="grossMarginPct" name="Gross Margin %" stroke={C.moss} strokeWidth={2} dot={{ r: 4 }} />
              <Line type="monotone" dataKey="opLossPct" name="Operating Margin %" stroke={C.clay} strokeWidth={2} dot={{ r: 4 }} />
            </LineChart>
          </ResponsiveContainer>
        </Panel>

        <Panel title="Cost Structure" sub="Cost of Sales vs Admin Expenses, EUR">
          <ResponsiveContainer width="100%" height={230}>
            <BarChart data={costData}>
              <CartesianGrid strokeDasharray="3 3" stroke={C.grid} vertical={false} />
              <XAxis dataKey="year" stroke={C.text} fontSize={12} fontFamily="IBM Plex Mono" />
              <YAxis stroke={C.text} fontSize={11} fontFamily="IBM Plex Mono" tickFormatter={(v) => `€${(v / 1000).toFixed(0)}k`} />
              <Tooltip contentStyle={tooltipStyle} formatter={(v) => fmtEUR(v)} />
              <Legend wrapperStyle={{ fontSize: 12, fontFamily: 'IBM Plex Sans' }} />
              <Bar dataKey="costOfSales" name="Cost of Sales" stackId="a" fill={C.clay} radius={[0, 0, 0, 0]} />
              <Bar dataKey="adminExpenses" name="Admin Expenses" stackId="a" fill={C.moss} radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </Panel>
      </div>

      <Panel title="P&L Summary" sub="FY2024 vs FY2025, EUR">
        <table className="data-table">
          <thead><tr><th style={{ textAlign: 'left' }}>Line item</th><th>FY2024</th><th>FY2025</th></tr></thead>
          <tbody>
            <tr><td>Turnover</td><td>{fmtEUR(f24.turnover)}</td><td>{fmtEUR(f25.turnover)}</td></tr>
            <tr><td>Gross Profit</td><td>{fmtEUR(f24.gross_profit)}</td><td>{fmtEUR(f25.gross_profit)}</td></tr>
            <tr><td>Admin Expenses</td><td className="negative">{fmtEUR(f24.admin_expenses)}</td><td className="negative">{fmtEUR(f25.admin_expenses)}</td></tr>
            <tr><td>Operating Profit/(Loss)</td><td className="negative">{fmtEUR(f24.operating_profit_loss)}</td><td className="negative">{fmtEUR(f25.operating_profit_loss)}</td></tr>
            <tr><td>Profit/(Loss) Before Tax</td><td className="negative">{fmtEUR(f24.profit_loss_before_tax)}</td><td className="negative">{fmtEUR(f25.profit_loss_before_tax)}</td></tr>
            <tr><td>Profit/(Loss) After Tax</td><td className="negative">{fmtEUR(f24.profit_loss_after_tax)}</td><td className="negative">{fmtEUR(f25.profit_loss_after_tax)}</td></tr>
          </tbody>
        </table>
      </Panel>
    </>
  )
}

/* -------------------------- CASH & LIQUIDITY -------------------------- */
export function CashLiquidity({ f24, f25, kpis, runway }) {
  const cashTrend = [
    { point: 'FY2024 start', cash: f24.cash_beginning },
    { point: 'FY2024 end', cash: f24.cash_end },
    { point: 'FY2025 end', cash: f25.cash_end },
    { point: 'Post-placement (pro-forma)', cash: runway.pro_forma_cash },
  ]

  const bridgeData = [
    { year: 'FY2024', operating: f24.cash_flow_operating, investing: f24.cash_flow_investing, financing: f24.cash_flow_financing },
    { year: 'FY2025', operating: f25.cash_flow_operating, investing: f25.cash_flow_investing, financing: f25.cash_flow_financing },
  ]

  const runwayKpi = findKpi(kpis, 'Cash Runway (book, FYE, pre-placement)')

  return (
    <>
      <SectionHeading eyebrow="Section 03" title="Cash & Liquidity" />

      <div className="kpi-grid">
        <KpiCard label="Cash at 30 June 2025" value={fmtEUR(f25.cash_end)} tone="negative" deltaLabel="↓ 67.0% YoY" />
        <KpiCard label="Net Cash Used in Operations" value={fmtEUR(f25.cash_flow_operating)}
          deltaLabel="↑ 67.9% improvement YoY" note="Negative value = cash outflow; improvement means a smaller outflow." />
        <KpiCard label="Book Cash Runway (pre-placement)" value={`${runwayKpi.fy2025} months`} tone="negative"
          note="FYE cash ÷ FY2025 average monthly operating burn." />
        <KpiCard label="Pro-forma Runway (post Dec-25 placement)" value={`${runway.pro_forma_runway_months} months`}
          tone="positive" note="Illustrative — includes €1.1m gross placement proceeds; assumes FY2025 burn rate holds." />
      </div>

      <div className="panel-grid-2">
        <Panel title="Cash Position Over Time" sub="EUR — including illustrative post-placement pro-forma">
          <ResponsiveContainer width="100%" height={230}>
            <AreaChart data={cashTrend}>
              <CartesianGrid strokeDasharray="3 3" stroke={C.grid} vertical={false} />
              <XAxis dataKey="point" stroke={C.text} fontSize={10} fontFamily="IBM Plex Mono" interval={0} angle={-12} textAnchor="end" height={60} />
              <YAxis stroke={C.text} fontSize={11} fontFamily="IBM Plex Mono" tickFormatter={(v) => `€${(v / 1000).toFixed(0)}k`} />
              <Tooltip contentStyle={tooltipStyle} formatter={(v) => fmtEUR(v)} />
              <Area type="monotone" dataKey="cash" stroke={C.moss} fill={C.moss} fillOpacity={0.18} strokeWidth={2} />
            </AreaChart>
          </ResponsiveContainer>
        </Panel>

        <Panel title="Cash Flow Bridge" sub="Operating / Investing / Financing, EUR">
          <ResponsiveContainer width="100%" height={230}>
            <BarChart data={bridgeData}>
              <CartesianGrid strokeDasharray="3 3" stroke={C.grid} vertical={false} />
              <XAxis dataKey="year" stroke={C.text} fontSize={12} fontFamily="IBM Plex Mono" />
              <YAxis stroke={C.text} fontSize={11} fontFamily="IBM Plex Mono" tickFormatter={(v) => `€${(v / 1000).toFixed(0)}k`} />
              <Tooltip contentStyle={tooltipStyle} formatter={(v) => fmtEUR(v)} />
              <Legend wrapperStyle={{ fontSize: 12, fontFamily: 'IBM Plex Sans' }} />
              <Bar dataKey="operating" name="Operating" fill={C.negative} />
              <Bar dataKey="investing" name="Investing" fill={C.clay} />
              <Bar dataKey="financing" name="Financing" fill={C.moss} />
            </BarChart>
          </ResponsiveContainer>
        </Panel>
      </div>

      <Panel title="Working Capital Components" sub="Only components explicitly disclosed — no full Current Ratio is computed, see note">
        <table className="data-table">
          <thead><tr><th style={{ textAlign: 'left' }}>Item</th><th>FY2024</th><th>FY2025</th></tr></thead>
          <tbody>
            <tr><td>Trade Debtors</td><td>{fmtEUR(f24.trade_debtors)}</td><td>{fmtEUR(f25.trade_debtors)}</td></tr>
            <tr><td>Trade Creditors</td><td>{fmtEUR(f24.trade_creditors)}</td><td>{fmtEUR(f25.trade_creditors)}</td></tr>
            <tr><td>New SBCI Term Loan (FY2025)</td><td>—</td><td>{fmtEUR(f25.new_bank_loan_sbci)}</td></tr>
          </tbody>
        </table>
        <p className="kpi-note" style={{ marginTop: 14 }}>
          The Information Document discloses these specific balance sheet line items in prose but not
          full current asset / current liability totals, so a standard Current Ratio cannot be computed
          without assuming figures not in the source — it is deliberately left out rather than estimated.
        </p>
      </Panel>
    </>
  )
}

/* ------------------------- SOLVENCY & LEVERAGE ------------------------- */
export function SolvencyLeverage({ f24, f25 }) {
  const equityTrend = [
    { year: 'FY2024', netAssets: f24.net_assets_liabilities },
    { year: 'FY2025', netAssets: f25.net_assets_liabilities },
  ]

  return (
    <>
      <SectionHeading eyebrow="Section 04" title="Solvency & Leverage" />
      <DisclosureBanner>
        Interest expense and the SBCI loan's amortisation schedule are not separately disclosed,
        so a <b>Debt Service Coverage Ratio cannot be reliably computed</b> — net finance cost and
        the loan balance are shown instead of an invented DSCR.
      </DisclosureBanner>

      <div className="kpi-grid">
        <KpiCard label="Net Assets / (Liabilities)" value={fmtEUR(f25.net_assets_liabilities)} tone="negative"
          note="Turned negative in FY2025 from net assets of €574,681 in FY2024." />
        <KpiCard label="Retained Earnings (deficit)" value={fmtEUR(f25.retained_earnings)} tone="negative" />
        <KpiCard label="New Secured Debt (FY2025)" value={fmtEUR(f25.new_bank_loan_sbci)} note="SBCI-backed term loan" />
        <KpiCard label="Net Finance Cost (FY2025)" value={fmtEUR(f25.profit_loss_before_tax - f25.operating_profit_loss)}
          note="PBT less Operating Loss — a small net finance cost, not separately itemised in the source." />
      </div>

      <Panel title="Net Assets / (Liabilities) Trend" sub="EUR — the balance sheet crossed into net liabilities in FY2025">
        <ResponsiveContainer width="100%" height={230}>
          <BarChart data={equityTrend}>
            <CartesianGrid strokeDasharray="3 3" stroke={C.grid} vertical={false} />
            <XAxis dataKey="year" stroke={C.text} fontSize={12} fontFamily="IBM Plex Mono" />
            <YAxis stroke={C.text} fontSize={11} fontFamily="IBM Plex Mono" tickFormatter={(v) => `€${(v / 1000).toFixed(0)}k`} />
            <Tooltip contentStyle={tooltipStyle} formatter={(v) => fmtEUR(v)} />
            <Bar dataKey="netAssets" radius={[4, 4, 0, 0]}>
              {equityTrend.map((d, i) => <Cell key={i} fill={d.netAssets >= 0 ? C.moss : C.negative} />)}
            </Bar>
          </BarChart>
        </ResponsiveContainer>
      </Panel>

      <Panel title="Why leverage metrics are limited here">
        <p style={{ fontSize: 13.5, color: 'var(--text-muted)', lineHeight: 1.7, margin: 0 }}>
          Senus is a pre-EBITDA-positive, early-stage business funded to date primarily through
          private placements and director loans rather than structured debt — the SBCI facility
          drawn in FY2025 is its first meaningful institutional debt. That means classic leverage
          ratios (Net Debt/EBITDA, DSCR, Interest Cover) either divide by a negative/near-zero
          denominator or rely on figures the Company has not yet disclosed at that granularity.
          This is normal for a company at this stage, and the Board should expect these metrics to
          become more meaningful — and should ask for the underlying disclosures — as the Company
          scales toward its stated FY2028 EBITDA-positive target.
        </p>
      </Panel>
    </>
  )
}

/* ------------------------------- RETURNS ------------------------------- */
export function Returns({ company, f24, f25 }) {
  return (
    <>
      <SectionHeading eyebrow="Section 05" title="Returns" />
      <DisclosureBanner>
        FY2025 closed with net liabilities of €(15,575) — capital employed is at or below zero, so
        <b> ROCE is not meaningful</b> for FY2025 (a small denominator makes the ratio swing wildly
        and would mislead rather than inform). It is intentionally omitted rather than shown.
      </DisclosureBanner>

      <div className="kpi-grid">
        <KpiCard label="Admission Share Price" value={`€${company.admission_share_price_eur}`} />
        <KpiCard label="Market Cap at Listing" value={fmtEUR(company.market_cap_at_listing_eur)} />
        <KpiCard label="Shares in Issue" value={company.shares_in_issue.toLocaleString()} />
        <KpiCard label="ROCE (FY2025)" value="Not meaningful" tone="negative" note="Capital employed ≈ €0 / negative" />
      </div>

      <Panel title="Context for the Board and Credit Providers">
        <p style={{ fontSize: 13.5, color: 'var(--text-muted)', lineHeight: 1.7, margin: 0 }}>
          Senus listed via Direct Listing at an implied valuation of €13.1m (post-money, based on
          the December 2025 Private Placement), against FY2025 revenue of {fmtEUR(f25.turnover)} —
          roughly a 15.7x revenue multiple, typical for an early-stage vertical software business
          with 78%+ gross margin trajectory but still pre-profitability. Traditional capital-return
          metrics (ROCE, ROE) will only become informative once the balance sheet returns to a
          positive equity position, which is itself a useful thing for the Board to track as a
          binary milestone rather than watching a misleading ratio in the meantime.
        </p>
      </Panel>
    </>
  )
}

/* ----------------------------- AI INSIGHTS ----------------------------- */
export function AIInsights() {
  const [section, setSection] = useState('overview')
  const [data, setData] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    setLoading(true)
    api.insights(section).then((d) => { setData(d); setLoading(false) })
  }, [section])

  const sections = ['overview', 'growth', 'profitability', 'cash', 'solvency', 'returns']

  return (
    <>
      <SectionHeading eyebrow="Section 06" title="AI-Generated Board Commentary" />
      <DisclosureBanner>
        This commentary is generated from the same audited dataset shown elsewhere in this report —
        it is instructed to cite only figures present in the data and to flag risk plainly rather
        than hedge. Treat it as a first draft for the Board, not a substitute for management's own
        narrative.
      </DisclosureBanner>

      <div style={{ display: 'flex', gap: 8, marginBottom: 20, flexWrap: 'wrap' }}>
        {sections.map((s) => (
          <button key={s} onClick={() => setSection(s)}
            className={`nav-item ${section === s ? 'active' : ''}`}
            style={{ display: 'inline-flex', width: 'auto' }}>
            {s[0].toUpperCase() + s.slice(1)}
          </button>
        ))}
      </div>

      <Panel>
        {loading ? (
          <p style={{ color: 'var(--text-muted)' }}>Generating commentary…</p>
        ) : (
          <>
            <div className="insight-box">{data.commentary}</div>
            <div className="insight-tag"><span className="dot" />{data.generated_by}</div>
          </>
        )}
      </Panel>
    </>
  )
}
