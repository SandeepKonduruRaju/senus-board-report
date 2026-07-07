# Senus PLC Board Report — One-Page Write-Up

**Brief:** Design and build an AI-native platform preparing a Board Report for
Senus PLC's Management, Board, Equity Investors, and Credit Providers.

## Approach

I treated this as a real financial-reporting product problem, not a data-viz
exercise. Step one was sourcing Senus's actual audited financials from their
public Information Document (the disclosure filed for their December 2025
Euronext Access Direct Listing) rather than inventing plausible-looking
numbers — a board report grounded in fabricated figures is worse than no
report at all. I then built a three-layer system: an AI-assisted extraction
pipeline that turns that PDF's prose-and-table financials into structured
JSON, a FastAPI + SQLite backend that computes board-level KPIs from that
data, and a React dashboard that presents it the way a CEO would actually use
it — by section (Growth, Profitability, Cash, Solvency, Returns), with an
AI-commentary layer that drafts board narrative directly from the same
numbers everyone else on the page is looking at.

## Technical decisions I'd stand over

**Structured extraction over free-text summarization.** The AI extraction
step uses Claude's `tool_use` with a strict JSON schema, not a "summarize this
PDF" prompt — because a schema-constrained extraction is checkable (you can
diff the output against the source table) in a way free text isn't. The model
is explicitly instructed to list anything it couldn't find rather than
estimate it.

**Flagging gaps instead of filling them.** Senus's summarised financials don't
disclose D&A separately, so EBITDA can't be reliably derived; they don't
disclose full current asset/liability totals, so a Current Ratio can't be
computed; and FY2025 closed with net liabilities, so ROCE isn't meaningful.
In each case the platform says so explicitly rather than showing an invented
or misleading number. I think this — knowing when *not* to show a metric — is
as much a part of "selecting appropriate financial metrics" as building the
ones that work.

**A functional deterministic fallback for the AI layer.** If no
`ANTHROPIC_API_KEY` is configured, the AI-commentary endpoint still returns
real, data-grounded commentary via a formatting function using the same
underlying dataset — so the platform's core value doesn't depend on a live
API call staying available, and the LLM version is a strict upgrade rather
than a dependency.

## AI tools used

Claude was used for: (1) the extraction pipeline design and the constrained
JSON-schema prompt that powers it, (2) drafting and iterating the FastAPI/
SQLAlchemy backend and React/Recharts frontend code, and (3) the live board
commentary the app itself generates at runtime. Every generated financial
figure was manually cross-checked against the source Information Document
before being committed to the dataset — see the README §3 and §6 for the
specifics of how, and where the process still relies on human review by
design.

## Validation

Every number in the seed dataset traces to a specific figure in Senus's
Information Document. Every metric shown on the dashboard is computed live
by the backend from that seed data — nothing is hardcoded in the frontend —
so any chart can be re-derived directly from the API. I ran the full stack
locally and hit every endpoint with `curl` against the actual source figures
before wiring up a single chart.
