const BASE = import.meta.env.VITE_API_BASE || '/api'

async function get(path) {
  const res = await fetch(`${BASE}${path}`)
  if (!res.ok) throw new Error(`API error ${res.status} on ${path}`)
  return res.json()
}

async function post(path, body) {
  const res = await fetch(`${BASE}${path}`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  })
  if (!res.ok) {
    const detail = await res.json().catch(() => ({}))
    throw new Error(detail.detail || `API error ${res.status} on ${path}`)
  }
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
  chat: (message, history) => post('/chat', { message, history }),
}
