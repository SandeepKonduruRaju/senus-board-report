"""
Chat tools — the functions Claude can call to answer questions about
Senus PLC's board data.

Design note: this is deliberately NOT "dump the whole dataset into the
prompt and let the model figure it out." Each tool is a narrow, named
query against the database, and the agent (see routers/chat.py) decides
which tools to call based on the question asked. This means:

  1. The model's context for any given answer is exactly the data it
     asked for — auditable, since the API response includes which tools
     were called and with what arguments.
  2. Tools can enforce their own guardrails (e.g. get_disclosure_gaps()
     exists specifically so the model has an explicit, correct answer to
     "what's the EBITDA/DSCR/ROCE" instead of being tempted to compute
     one from raw figures it was handed).
  3. Each tool is a plain Python function — testable with pytest without
     needing an API key or mocking an LLM call at all.
"""
from typing import Any

from sqlalchemy.orm import Session

from . import models

# ---------------------------------------------------------------------------
# Tool implementations
# ---------------------------------------------------------------------------


def get_annual_financials(db: Session, fiscal_year: str) -> dict[str, Any]:
    """Full figures for one reporting period.

    fiscal_year must be one of: FY2024, H1_FY2025, FY2025, H1_FY2026
    """
    row = db.query(models.AnnualFinancial).filter_by(fiscal_year=fiscal_year).first()
    if row is None:
        valid = [r.fiscal_year for r in db.query(models.AnnualFinancial).all()]
        return {"error": f"No data for {fiscal_year!r}. Valid periods: {valid}"}
    return {c.name: getattr(row, c.name) for c in row.__table__.columns}


def list_periods(db: Session) -> dict[str, Any]:
    """List every reporting period available, with headline revenue/status."""
    rows = db.query(models.AnnualFinancial).order_by(models.AnnualFinancial.period_end).all()
    return {
        "periods": [
            {
                "fiscal_year": r.fiscal_year,
                "period_label": r.period_label,
                "period_end": r.period_end,
                "is_half_year": r.is_half_year,
                "is_preliminary": r.is_preliminary,
                "turnover": r.turnover,
            }
            for r in rows
        ]
    }


def get_company_profile(db: Session) -> dict[str, Any]:
    """Static company metadata: ticker, ISIN, listing details, employee count."""
    c = db.query(models.Company).first()
    if c is None:
        return {"error": "No company record found"}
    return {col.name: getattr(c, col.name) for col in c.__table__.columns}


def get_strategy_targets(db: Session) -> dict[str, Any]:
    """The Board-stated Senus 2030 strategic targets."""
    t = db.query(models.StrategyTarget).first()
    if t is None:
        return {"error": "No strategy targets found"}
    return {c.name: getattr(t, c.name) for c in t.__table__.columns}


def get_post_period_events(db: Session) -> dict[str, Any]:
    """Material events after each balance sheet date (acquisitions, placements, listing)."""
    rows = db.query(models.PostPeriodEvent).order_by(models.PostPeriodEvent.date).all()
    return {
        "events": [
            {"date": r.date, "event": r.event, "detail": r.detail,
             "gross_proceeds_eur": r.gross_proceeds_eur}
            for r in rows
        ]
    }


def get_disclosure_gaps(db: Session) -> dict[str, Any]:
    """
    The authoritative answer for 'why isn't X metric shown' questions.

    This tool exists specifically so the model has a correct, pre-written
    answer for EBITDA/DSCR/ROCE/Current-Ratio questions instead of being
    tempted to derive one from raw figures it was handed — the same
    principle applied throughout the dashboard itself.
    """
    return {
        "gaps": [
            {
                "metric": "EBITDA",
                "why_not_shown": (
                    "D&A is not broken out from admin expenses in the FY2024/FY2025 "
                    "audited financials (H1 FY2026 does disclose depreciation of "
                    "EUR 10,014, but only for that period, so it can't be shown "
                    "consistently across all periods). Operating Loss is shown instead."
                ),
            },
            {
                "metric": "ROCE",
                "why_not_shown": (
                    "FY2025 closed with net liabilities of EUR (15,575) — capital "
                    "employed is near zero/negative, making the ratio swing wildly "
                    "and potentially mislead. Net assets turned positive again in "
                    "H1 FY2026 (EUR 561,081), so this is a point-in-time flag."
                ),
            },
            {
                "metric": "DSCR",
                "why_not_shown": (
                    "No loan amortisation schedule is disclosed in any period. "
                    "H1 FY2026 does disclose interest payable (EUR 1,391) for the "
                    "first time, but that alone isn't enough to compute a genuine "
                    "debt service coverage ratio."
                ),
            },
            {
                "metric": "Current Ratio",
                "why_not_shown": (
                    "FY2024/FY2025 disclose only specific balance sheet components "
                    "(debtors, creditors, cash), not full current asset/liability "
                    "totals. H1 FY2026 does disclose full totals (current assets "
                    "EUR 923,339; current liabilities EUR 387,105 trade + EUR "
                    "850,000 Loamin contingent consideration), giving a computable "
                    "ratio of ~0.75x for that period specifically — below 1.0x, "
                    "largely a function of the newly-recognised Loamin earn-out "
                    "rather than a change in underlying trading liquidity."
                ),
            },
        ]
    }


# ---------------------------------------------------------------------------
# Tool registry: name -> (JSON schema for the LLM, callable)
# ---------------------------------------------------------------------------

TOOL_SCHEMAS: list[dict[str, Any]] = [
    {
        "name": "get_annual_financials",
        "description": (
            "Get full audited/reported figures for one specific reporting period "
            "(income statement, balance sheet, cash flow). Use list_periods first "
            "if you don't know the exact fiscal_year key to use."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "fiscal_year": {
                    "type": "string",
                    "description": "One of: FY2024, H1_FY2025, FY2025, H1_FY2026",
                }
            },
            "required": ["fiscal_year"],
        },
    },
    {
        "name": "list_periods",
        "description": "List every reporting period available with headline revenue and status flags.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_company_profile",
        "description": "Get static company metadata: ticker, ISIN, exchange, listing date, employees.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_strategy_targets",
        "description": "Get the Board-stated Senus 2030 (FY2026-2030) strategic targets.",
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_post_period_events",
        "description": (
            "Get material events after each period's balance sheet date, e.g. the "
            "Loamin acquisition, the December 2025 Private Placement, the Direct "
            "Listing, and the H1 FY2026 results publication."
        ),
        "input_schema": {"type": "object", "properties": {}},
    },
    {
        "name": "get_disclosure_gaps",
        "description": (
            "Call this whenever asked about EBITDA, ROCE, DSCR, or Current Ratio — "
            "it returns the authoritative explanation for why each is or isn't "
            "shown, rather than deriving a figure yourself from raw data."
        ),
        "input_schema": {"type": "object", "properties": {}},
    },
]

TOOL_FUNCTIONS = {
    "get_annual_financials": get_annual_financials,
    "list_periods": list_periods,
    "get_company_profile": get_company_profile,
    "get_strategy_targets": get_strategy_targets,
    "get_post_period_events": get_post_period_events,
    "get_disclosure_gaps": get_disclosure_gaps,
}


def call_tool(db: Session, name: str, tool_input: dict[str, Any]) -> dict[str, Any]:
    """Dispatch a tool call by name. Returns an error dict for unknown tools
    rather than raising, so a bad tool call degrades gracefully in the
    conversation instead of crashing the whole request."""
    fn = TOOL_FUNCTIONS.get(name)
    if fn is None:
        return {"error": f"Unknown tool: {name!r}"}
    return fn(db, **tool_input)
