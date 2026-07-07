# Senus PLC — Board Report Platform

An AI-native board reporting platform built for the Assiduous Technology Graduate
Assessment, using Senus PLC's actual audited FY2024/FY2025 financials (Euronext
Access Direct Listing, December 2025).

**Live demo:** [add your deployed URL here]
**Video walkthrough:** [add your YouTube link here]

---

## 1. What this is

A full-stack web application that a CEO, Board member, equity investor, or credit
provider could log into to understand Senus's financial performance: growth,
profitability, cash and liquidity, solvency, and returns — plus an AI commentary
layer that drafts board-ready narrative directly from the underlying numbers.

It is built around one non-negotiable rule: **every figure in the app traces back
to a disclosed number in Senus's Information Document**, and anywhere a standard
metric (EBITDA, Current Ratio, DSCR, ROCE) can't be reliably computed from what
the Company has actually disclosed, the app says so explicitly instead of
inventing a number. That's a deliberate product decision, not a limitation I
missed — a board report that quietly fabricates an EBITDA figure is worse than
one that has a gap in it.

## 2. Architecture

```
senus-board-report/
├── backend/                    FastAPI service
│   ├── app/
│   │   ├── main.py             App entrypoint, CORS, router registration
│   │   ├── database.py         SQLAlchemy engine/session (SQLite by default)
│   │   ├── models.py           ORM models: Company, AnnualFinancial,
│   │   │                       PostPeriodEvent, StrategyTarget
│   │   ├── schemas.py          Pydantic response contracts
│   │   └── routers/
│   │       ├── financials.py   Raw + derived KPI endpoints
│   │       └── insights.py     AI commentary endpoint (+ deterministic fallback)
│   └── data/
│       ├── senus_financials.json   Extracted structured dataset (see §3)
│       ├── extract_financials.py   The AI extraction pipeline itself
│       └── seed_db.py              Loads the JSON into the database
│
└── frontend/                   React + Vite dashboard
    └── src/
        ├── App.jsx              Shell: sidebar nav, header, section routing
        ├── api.js                Thin fetch client for the backend
        └── components/
            ├── Sections.jsx      Overview / Growth / Profitability / Cash /
            │                     Solvency / Returns / AI Insights
            └── ui.jsx            KPI cards, panels, formatting helpers
```

**Why this split:** the brief specifically asks for "AI methods for extracting
financial information from the source documents into a database powering a
model" — so the pipeline that turns a PDF into structured data (`data/`) is
kept separate from the API that serves it (`app/`) and the UI that presents it
(`frontend/`). Each layer can be tested, replaced, or extended independently —
e.g. swapping SQLite for Postgres is a one-line change to `DATABASE_URL`, and
adding a new fiscal year (once Senus reports H1/FY2026) means re-running the
extraction script and `seed_db.py`, with zero frontend changes required.

**Stack choices and why:**
- **FastAPI** — typed request/response contracts (Pydantic), auto-generated
  OpenAPI docs at `/docs`, and async-ready if the insights endpoint needs to
  call an external LLM API without blocking.
- **SQLAlchemy + SQLite** — a real relational schema (not just a JSON blob
  behind an API) so the "database powering a model" requirement is genuine,
  while staying zero-config for a graduate assessment. `DATABASE_URL` swaps to
  Postgres for production with no code changes.
- **React + Vite** — fast dev loop, and Recharts for the visualizations since
  it composes cleanly with React state rather than requiring imperative chart
  re-renders.
- **No auth layer** — deliberately out of scope for this assessment; in a real
  deployment this would sit behind Senus's identity provider before Board/investor
  data went anywhere near it.

## 3. AI-assisted data extraction — how the numbers got into the database

This is the part of the brief I want to be very precise about, since it's the
part most likely to raise a "how do I know this data is real" question.

**Source:** the Senus PLC Information Document (December 2025), the company's
own disclosure document for its Direct Listing — the same document referenced
on the Senus investor relations page. It contains audited FY2024 and FY2025
figures.

**Extraction method:** `backend/data/extract_financials.py` implements the
actual pipeline: it sends raw document text to Claude with a constrained
`tool_use` schema (`record_annual_financials`), so the model can only return
JSON in the exact shape the database expects — it cannot free-text a summary
or an interpretation. The system prompt explicitly instructs the model to
extract only values that are stated or trivially derivable (e.g.
`cost_of_sales = turnover − gross_profit`), and to list anything it expected
but couldn't find in `fields_not_found` rather than estimate it.

**How the shipped dataset was actually built:** I extracted the FY2024/FY2025
figures from the Information Document using this LLM-assisted approach, then
manually cross-checked every figure in `senus_financials.json` against the
source PDF before committing it — line by line, not spot-checked. That
manual verification step is why I'm confident defending any number in this
app; the AI accelerated transcription, it didn't replace review. The pipeline
script is fully functional and will run against `ANTHROPIC_API_KEY` on any new
disclosure Senus publishes (e.g. FY2026 half-year results) — I could not
locate a distinct H1 FY2026 filing as its own document at the time of
building this, so the platform is scoped to FY2024/FY2025 actuals plus the
Board's own stated FY2026-2030 targets ("Senus 2030"), and is built so a new
period slots in via `extract_financials.py` → review the diff → `seed_db.py`,
with no schema or frontend change.

**Why `tool_use` and not just asking the model to "summarize the PDF":** a
free-text extraction can quietly drop a sign, round a number, or paraphrase a
figure into something that reads plausibly but isn't what the source said. A
strict schema with `required` fields and explicit "don't guess" instructions
converts extraction into something checkable — you can diff the tool call
output against the source table directly.

## 4. AI-generated commentary (the "AI-powered insights" requirement)

`GET /api/insights?section=<name>` generates board commentary. If
`ANTHROPIC_API_KEY` is set, it calls Claude with the full audited dataset for
that section and instructs it to cite only figures present in that data,
state risk plainly rather than hedge, and stay under 220 words. If no key is
set, it falls back to a deterministic function
(`_static_fallback` in `insights.py`) that formats the same figures into the
same voice without an LLM call — so the app is fully functional, and the AI
layer is additive rather than a single point of failure. I'd recommend
demoing with the API key set, since the LLM version adapts its framing
per-section in a way the fallback (intentionally) doesn't.

## 5. Key assumptions & judgement calls

I'd rather list these explicitly than have them discovered:

- **EBITDA is not shown.** Depreciation & amortisation isn't broken out from
  administrative expenses in Senus's summarised financials, so any EBITDA
  figure would require an assumed D&A add-back. I chose not to invent one —
  Operating Loss is shown as the closest genuinely disclosed proxy, with a
  visible note explaining why.
- **ROCE is flagged as "not meaningful" for FY2025**, because the Company
  closed the year with net liabilities of €(15,575) — a near-zero/negative
  capital employed figure makes the ratio swing wildly and would mislead a
  reader rather than inform them.
- **DSCR is not shown.** Interest expense and the SBCI loan's repayment
  schedule aren't separately disclosed, so it can't be computed reliably.
- **Current Ratio / full working capital is not shown**, for the same reason —
  only specific components (trade debtors, trade creditors, cash) are
  disclosed in the source, not full current asset/liability totals.
- **The "pro-forma cash runway" figure is explicitly labelled illustrative.**
  It combines the FY2025 closing cash position with the gross (not
  net-of-fees) December 2025 Private Placement proceeds, assuming the FY2025
  burn rate continues unchanged — which the Board's own growth investment
  plans make unlikely. It's shown because it's a natural question a Board
  would ask, but every place it appears says clearly that it's a model, not a
  disclosed figure.
- **The Senus 2030 revenue trajectory chart is a target model, not a
  forecast** — it mechanically compounds the Board's own stated 50% CAGR
  floor from the FY2025 base, purely to give the Board a visual sense of what
  that target implies year by year.

## 6. How I validated the outputs

1. Every number in `senus_financials.json` was checked against the specific
   page/section of the Information Document it came from before being
   committed (see §3).
2. Every derived metric (YoY %, margin percentage-point deltas, cash runway)
   is computed live by the backend from those base figures — nothing is
   hardcoded in the frontend — so a reviewer can re-derive any chart from
   `GET /api/financials/annual` alone.
3. `sanity_check()` in `extract_financials.py` runs basic plausibility checks
   (e.g. gross profit can't exceed turnover) on any newly-extracted record
   before it's allowed near the database.
4. I ran the full stack locally end-to-end (backend on :8000, frontend on
   :5173 via the Vite proxy) and hit every API endpoint directly with `curl`
   to confirm the JSON matched the source figures before wiring up any chart.

## 7. Running it locally

**Backend:**
```bash
cd backend
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m data.seed_db          # creates and seeds senus.db
uvicorn app.main:app --reload   # http://localhost:8000
```

**Frontend** (separate terminal):
```bash
cd frontend
npm install
npm run dev                     # http://localhost:5173
```

The Vite dev server proxies `/api/*` to `localhost:8000` (see
`vite.config.js`), so just open `http://localhost:5173`.

To enable live AI commentary rather than the deterministic fallback:
```bash
export ANTHROPIC_API_KEY=sk-ant-...
```

## 8. Deploying it (for the demo video / live link)

- **Backend** → Render / Railway / Fly.io: point at `backend/`, start command
  `uvicorn app.main:app --host 0.0.0.0 --port $PORT`, set `ANTHROPIC_API_KEY`
  as an environment variable if you want live AI commentary.
- **Frontend** → Vercel / Netlify: point at `frontend/`, build command
  `npm run build`, output directory `dist`, and set `VITE_API_BASE` to your
  deployed backend URL (e.g. `https://senus-api.onrender.com/api`).

## 9. What I'd build next with more time

- A proper document-diff view so the Board can see exactly which sentence in
  a new disclosure produced which number, rather than trusting the pipeline.
- Multi-period support once Senus publishes FY2026 interim/full-year results,
  with genuine trend lines instead of a two-point FY2024→FY2025 comparison.
- Role-based views — a credit provider cares about liquidity and covenant
  headroom first; an equity investor cares about growth and TAM narrative
  first. Right now everyone sees the same sections in the same order.
