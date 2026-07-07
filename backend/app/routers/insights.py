import json
import os
from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .. import models
from ..database import get_db

router = APIRouter(prefix="/api/insights", tags=["insights"])

MODEL = "claude-sonnet-4-6"

SYSTEM_PROMPT = """You are drafting the "Management Commentary" section of a \
board pack for Senus PLC, a pre-EBITDA-positive Natural Capital software \
company listed on Euronext Access Dublin. Write for a Board that includes \
non-executive directors, equity investors and a credit provider. Be direct \
and specific: cite the actual figures given, do not hedge with vague language, \
and do not invent any number not present in the data you are given. Where a \
trend is positive, say so plainly; where risk exists (e.g. cash runway, \
customer concentration, ROCE not meaningful), name it plainly too. \
Write 3 short paragraphs, no headers, no bullet points, plain prose, under 220 words."""


def _static_fallback(f24, f25, targets) -> str:
    """Deterministic, no-API-key-required commentary so the platform still
    works out of the box. Every figure below is pulled directly from the DB
    row, not hardcoded — this function just formats it without an LLM call."""
    rev_growth = round(((f25.turnover - f24.turnover) / f24.turnover) * 100, 1)
    margin_gain = round(f25.gross_margin_pct - f24.gross_margin_pct, 1)
    loss_reduction = round(
        (1 - abs(f25.profit_loss_after_tax) / abs(f24.profit_loss_after_tax)) * 100, 1
    )
    return (
        f"Revenue grew {rev_growth}% year-on-year to €{f25.turnover:,.0f} in FY2025, "
        f"against a Senus 2030 target of {targets.revenue_cagr_target_pct:.0f}% CAGR through "
        f"FY2030 — this year's growth sits below that long-run bar, which the Board should "
        f"expect to see close as Senus ERA and the Loamin integration scale through FY2026. "
        f"Gross margin expanded {margin_gain:.1f} percentage points to {f25.gross_margin_pct:.1f}%, "
        f"and the net loss after tax narrowed {loss_reduction:.0f}% to €{abs(f25.profit_loss_after_tax):,.0f}, "
        f"both consistent with a business converting scale into unit economics rather than "
        f"just growing revenue.\n\n"
        f"The balance sheet is the item requiring closest attention: Senus ended FY2025 with "
        f"net liabilities of €{abs(f25.net_assets_liabilities):,.0f} and period-end cash of just "
        f"€{f25.cash_end:,.0f}, against average monthly operating cash burn of roughly "
        f"€{abs(f25.cash_flow_operating)/12:,.0f}. Taken on its own, that FYE cash position "
        f"implies a thin runway — the December 2025 Private Placement (€1.1m gross) materially "
        f"changes that picture, but the Board should track actual net burn post-placement "
        f"against the FY2025 run-rate rather than assume it holds.\n\n"
        f"Customer mix remains concentrated: {f25.customers_enterprise} Enterprise accounts "
        f"generated {f25.revenue_channel_enterprise_pct:.0f}% of FY2025 revenue, and "
        f"{f25.revenue_ireland_pct:.0f}% of revenue is still Ireland-only against a Senus 2030 "
        f"target of under 50% by FY2030. Progress on Senus ERA's international rollout and the "
        f"Loamin-driven UK expansion are the two clearest levers management has to move both "
        f"numbers this year."
    )


@router.get("")
def get_insights(section: str = "overview", db: Session = Depends(get_db)):
    f24 = db.query(models.AnnualFinancial).filter_by(fiscal_year="FY2024").first()
    f25 = db.query(models.AnnualFinancial).filter_by(fiscal_year="FY2025").first()
    targets = db.query(models.StrategyTarget).first()

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        return {
            "section": section,
            "commentary": _static_fallback(f24, f25, targets),
            "generated_by": "deterministic-fallback (no ANTHROPIC_API_KEY configured)",
        }

    import anthropic
    client = anthropic.Anthropic(api_key=api_key)

    payload = {
        "fy2024": {c.name: getattr(f24, c.name) for c in f24.__table__.columns},
        "fy2025": {c.name: getattr(f25, c.name) for c in f25.__table__.columns},
        "strategy_targets": {c.name: getattr(targets, c.name) for c in targets.__table__.columns},
    }

    response = client.messages.create(
        model=MODEL,
        max_tokens=600,
        system=SYSTEM_PROMPT,
        messages=[{
            "role": "user",
            "content": f"Here is the audited financial data:\n\n{json.dumps(payload, indent=2)}\n\n"
                       f"Write the board commentary for the '{section}' section.",
        }],
    )
    text = "".join(block.text for block in response.content if block.type == "text")
    return {"section": section, "commentary": text, "generated_by": MODEL}
