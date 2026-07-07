const BASE = import.meta.env.VITE_API_BASE || '/api'

async function get(path) {
  const res = await fetch(`${BASE}${path}`)
  if (!res.ok) throw new Error(`API error ${res.status} on ${path}`)
  return res.json()
}

export const api = {
  company: () => get('/financials/company'),
  annual: () => get('/financials/annual'),
  kpis: () => get('/financials/kpis'),
  proFormaRunway: () => get('/financials/pro-forma-runway'),
  strategyTargets: () => get('/financials/strategy-targets'),
  postPeriodEvents: () => get('/financials/post-period-events'),
  insights: (section) => get(`/insights?section=${section}`),
}
