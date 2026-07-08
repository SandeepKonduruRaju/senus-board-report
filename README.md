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

**Source:** two documents. (1) The Senus PLC Information Document (December
2025) — the company's Direct Listing disclosure — for audited FY2024/FY2025
figures. (2) The Senus PLC Half Year Results for the six months ended 31
December 2025 (published 19 March 2026), for H1 FY2026 and the H1 FY2025
comparative period. Both are the company's own primary-source filings.

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
source PDF before committing it — line by line, not spot-checked. The H1
FY2026 filing (and its H1 FY2025 comparative column) is distributed via an
authenticated investor portal and isn't reachable by public web search or
fetch tools — I obtained the filing directly and applied the same
line-by-line cross-check against its P&L, Balance Sheet, and Cash Flow
Statement before adding it. That manual verification step is why I'm
confident defending any number in this app; the AI accelerated transcription,
it didn't replace review. The extraction script will run unattended against
`ANTHROPIC_API_KEY` on any future disclosure Senus publishes (e.g. FY2026
full-year results) — a new period slots in via `extract_financials.py` →
review the diff → `seed_db.py`, with no schema or frontend change, exactly as
happened when H1 FY2026 was added after the initial build.

**A concrete example of why the manual cross-check matters:** the platform
originally shipped an *illustrative* pro-forma cash runway estimate (FY2025
cash + gross placement proceeds, FY2025 burn rate assumed) before H1 FY2026
results existed. Once the actual H1 FY2026 figures were added, the real cash
position came in lower than that estimate — not because the estimate was
wrong given what was known at the time, but because H1 operating burn came in
materially higher (Loamin integration costs) and a loan repayment wasn't
anticipated. Rather than quietly replace the old estimate, the Cash &
Liquidity section shows both side by side with an explanation of the
variance — this is the kind of thing a Board should see, not something a
dashboard should paper over.

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

- **EBITDA is not shown as a headline metric.** D&A isn't broken out from
  administrative expenses in the FY2024/FY2025 summarised financials (H1
  FY2026 does disclose depreciation of €10,014, but only for that period) —
  rather than show EBITDA for some periods and not others on an inconsistent
  basis, Operating Loss is shown throughout as the closest genuinely
  disclosed proxy.
- **ROCE is flagged as "not meaningful" for FY2025 specifically**, because
  the Company closed that year with net liabilities of €(15,575) — a
  near-zero/negative capital employed figure makes the ratio swing wildly.
  Net assets turned positive again in H1 FY2026 (€561,081), so this is a
  point-in-time flag, not a permanent one.
- **DSCR is still not shown**, even though H1 FY2026 discloses interest
  payable (€1,391) for the first time — no loan amortisation schedule is
  available in any period, so a genuine debt service coverage figure still
  can't be computed reliably.
- **Current Ratio is now computable from H1 FY2026 onward**, since that
  filing discloses full current assets (€923,339) and current liabilities
  (€387,105 trade + €850,000 contingent consideration for Loamin) — a ratio
  of ~0.75×. It's shown for H1 FY2026 only, with a note that it's driven
  largely by the newly-recognised Loamin earn-out rather than a change in
  underlying trading liquidity. It's still not shown for FY2024/FY2025,
  which only disclose specific components, not full totals.
- **The "pro-forma cash runway" estimate is shown alongside the actual H1
  FY2026 outcome, not replaced by it.** The original illustrative estimate
  (FY2025 cash + gross placement proceeds, FY2025 burn rate assumed) came in
  higher than what H1 FY2026 actually delivered — operating burn rose
  materially post-Loamin, and a €124,837 loan repayment wasn't in the
  original assumption. Rather than quietly update the number, both are shown
  with an explanation of the variance — this is the more honest way to
  present an estimate that later turned out to be wrong for good reasons.
- **The Senus 2030 revenue trajectory chart is a target model, not a
  forecast** — it mechanically compounds the Board's own stated 50% CAGR
  floor from the FY2025 base, purely to give the Board a visual sense of what
  that target implies year by year.
- **Login is a hardcoded credential gate, not real authentication.** Three
  demo accounts (CEO / Board / Analyst, all password `senus2030`) exist purely
  to satisfy "a platform a CEO would log in to and use" for this assessment.
  A production deployment would sit behind Senus's actual identity provider —
  this is explicitly out of scope, not an oversight.

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

**Logging in:** the dashboard sits behind a credential gate (see §5 —
hardcoded for this assessment, not real auth). Use any of:

| Username | Password    |
|----------|-------------|
| CEO      | senus2030   |
| Board    | senus2030   |
| Analyst  | senus2030   |

## 7a. Running the test suite

```bash
cd backend
pip install -r requirements-dev.txt
pytest tests/ -v          # 17 tests: endpoints, KPI math, extraction guardrails
flake8 app/ data/          # lint
```

Tests run against an isolated temp-file SQLite database (see
`tests/conftest.py`), seeded via the same `seed_db.seed()` the real app
uses — so they exercise the real seeding path, not a hand-rolled fixture
that could quietly drift from it.

One of these tests already earned its keep during development: an earlier
version of `extract_financials.py`'s validation logic flagged Senus's real
FY2025 tax credit (PAT less negative than PBT) as a "sign convention error"
— which is wrong; a tax credit legitimately produces that pattern. The test
`test_sanity_check_passes_valid_record` caught this as a false positive
against real audited data, which is why the check was rewritten to look at
the *size* of a tax adjustment relative to PBT instead of its direction —
see the docstring in `extract_financials.py::sanity_check` for the full story.

CI (`.github/workflows/ci.yml`) runs this test suite plus `flake8` on the
backend and `npm run build` on the frontend for every push and pull request.

## 8. Deploying it (for the demo video / live link)

- **Backend** → Render / Railway / Fly.io: point at `backend/`, start command
  `uvicorn app.main:app --host 0.0.0.0 --port $PORT`, set `ANTHROPIC_API_KEY`
  as an environment variable if you want live AI commentary.
- **Frontend** → Vercel / Netlify: point at `frontend/`, build command
  `npm run build`, output directory `dist`, and set `VITE_API_BASE` to your
  deployed backend URL (e.g. `https://senus-api.onrender.com/api`).

## 9. Version control workflow

This repo uses a simple two-branch model, appropriate for a solo project with
a real review step rather than a full GitFlow setup that would be overkill
here:

- **`main`** — always deployable. Only receives merges via reviewed pull
  request, never direct commits.
- **`dev`** — integration branch for work in progress. All feature work
  (the login screen, source tooltips, H1 FY2026 data integration, etc.) is
  committed here first.

Workflow: commit to `dev` → open a PR from `dev` into `main` → review the
diff (self-review is still a review — re-reading your own diff before it
hits `main` catches mistakes a same-sitting "looks good" pass misses) → merge.
This is a genuine PR, not a formality: it's where you'd catch something like
a hardcoded value that should have come from the API, or a copy-paste error
in a disclosure note.

```bash
git checkout dev
git add .
git commit -m "feat: add login gate, source tooltips, H1 FY2026 data"
git push origin dev

# Then open a PR dev → main on GitHub, review, and merge.
# For subsequent work, branch again from dev:
git checkout -b feature/role-based-views dev
```

Is a PR *required* for a solo assessment project? No — but using one signals
the same engineering discipline the brief asks for ("production-quality
engineering practices"), and it gives you a clean, reviewable diff to point
to if asked "walk me through what you changed and why" in an interview.

## 10. What I'd build next with more time

- A proper document-diff view so the Board can see exactly which sentence in
  a new disclosure produced which number, rather than trusting the pipeline —
  useful now that the platform has already absorbed one new filing (H1
  FY2026) after initial build.
- Real authentication (OAuth/SAML against Senus's identity provider) in place
  of the hardcoded login gate, plus per-user audit logging of who viewed what.
- Role-based views — a credit provider cares about liquidity and covenant
  headroom first; an equity investor cares about growth and TAM narrative
  first. Right now everyone sees the same sections in the same order.
- A genuine Current Ratio and DSCR the moment Senus's reporting granularity
  supports it consistently across periods (H1 FY2026 already discloses more
  than FY2024/FY2025 did — see §5) — the schema is already built to support
  this without migration.
- Automated regression tests (`pytest` + `TestClient`) codifying the manual
  endpoint checks done during development, so a future data update can't
  silently break a derived KPI calculation.
