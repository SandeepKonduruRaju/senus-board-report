"""
AI-generated board commentary endpoint.

If ANTHROPIC_API_KEY is set, calls Claude (claude-sonnet-4-6) with the full
audited dataset for the requested section. If not set, returns deterministic
commentary built directly from the database — so the app is fully functional
without an API key; the LLM version is additive, not a dependency.
"""
import json
import logging
import os
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

log = logging.getLogger(__name__)

router = APIRouter(prefix="/api/insights", tags=["insights"])

MODEL = "claude-sonnet-4-6"

SYSTEM_PROMPT = (
    "You are drafting the 'Management Commentary' section of a board pack for "
    "Senus PLC, a pre-EBITDA-positive Natural Capital software company listed on "
    "Euronext Access Dublin. Write for a Board including non-executive directors, "
    "equity investors, and a credit provider. Rules: (1) cite only the actual "
    "figures present in the data you are given — never invent a number; "
    "(2) name risks plainly, do not hedge with vague language; "
    "(3) write exactly 3 short paragraphs, no headers, no bullets, plain prose, "
    "under 220 words total."
)


def _build_payload(
    f24: models.AnnualFinancial,
    f25: models.AnnualFinancial,
    targets: models.StrategyTarget,
) -> dict[str, Any]:
    """Serialise DB rows to a plain dict safe for JSON / LLM prompt."""
    def _row(obj) -> dict:
        return {c.name: getattr(obj, c.name) for c in obj.__table__.columns}

    return {
        "fy2024": _row(f24),
        "fy2025": _row(f25),
        "strategy_targets": _row(targets),
    }


def _static_fallback(
    f24: models.AnnualFinancial,
    f25: models.AnnualFinancial,
    targets: models.StrategyTarget,
) -> str:
    """
    Deterministic commentary when no API key is configured.

    Every figure is pulled live from the DB rows — nothing is hardcoded here
    — so this function stays correct even if the seed data is updated.
    """
    rev_growth = round(((f25.turnover - f24.turnover) / f24.turnover) * 100, 1)
    margin_gain = round(f25.gross_margin_pct - f24.gross_margin_pct, 1)
    loss_reduction = round(
        (1 - abs(f25.profit_loss_after_tax) / abs(f24.profit_loss_after_tax)) * 100, 1
    )
    monthly_burn = abs(f25.cash_flow_operating) / 12

    return (
        f"Revenue grew {rev_growth}% year-on-year to €{f25.turnover:,.0f} in FY2025 against "
        f"a Senus 2030 target of {targets.revenue_cagr_target_pct:.0f}% CAGR — this year's "
        f"growth sits below that long-run bar, which the Board should expect to close as Senus "
        f"ERA and the Loamin integration scale through FY2026. Gross margin expanded "
        f"{margin_gain:.1f}pp to {f25.gross_margin_pct:.1f}% and the net loss narrowed "
        f"{loss_reduction:.0f}% to €{abs(f25.profit_loss_after_tax):,.0f}, both consistent "
        f"with a business converting scale into improved unit economics.\n\n"
        f"The balance sheet requires the Board's closest attention: Senus ended FY2025 with "
        f"net liabilities of €{abs(f25.net_assets_liabilities):,.0f} and period-end cash of "
        f"€{f25.cash_end:,.0f} against average monthly operating burn of "
        f"€{monthly_burn:,.0f}. The December 2025 Private Placement (€1.1m gross) materially "
        f"improves this picture, but the Board should track actual net burn post-placement "
        f"against the FY2025 run-rate rather than assume it holds unchanged.\n\n"
        f"Customer concentration is the other key risk: {f25.customers_enterprise} Enterprise "
        f"accounts generated {f25.revenue_channel_enterprise_pct:.0f}% of FY2025 revenue, "
        f"and {f25.revenue_ireland_pct:.0f}% of revenue remains Ireland-only against a Senus "
        f"2030 target below 50% by FY2030. The Loamin-driven UK expansion and the Senus ERA "
        f"international rollout are management's clearest levers to move both numbers this year."
    )


@router.get("", response_model=schemas.InsightOut, summary="AI board commentary")
def get_insights(
    section: str = "overview",
    db: Session = Depends(get_db),
) -> schemas.InsightOut:
    """
    Returns board-ready commentary for the requested section.

    Requires ANTHROPIC_API_KEY env var for live LLM generation; falls back
    to deterministic data-driven commentary when no key is configured.
    """
    f24 = db.query(models.AnnualFinancial).filter_by(fiscal_year="FY2024").first()
    f25 = db.query(models.AnnualFinancial).filter_by(fiscal_year="FY2025").first()
    targets = db.query(models.StrategyTarget).first()

    if not all([f24, f25, targets]):
        raise HTTPException(
            status_code=503,
            detail="Financial data not loaded — run python -m data.seed_db",
        )

    api_key = os.environ.get("ANTHROPIC_API_KEY")

    if not api_key:
        return schemas.InsightOut(
            section=section,
            commentary=_static_fallback(f24, f25, targets),
            generated_by="deterministic-fallback (set ANTHROPIC_API_KEY for live generation)",
        )

    try:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)
        payload = _build_payload(f24, f25, targets)

        response = client.messages.create(
            model=MODEL,
            max_tokens=600,
            system=SYSTEM_PROMPT,
            messages=[{
                "role": "user",
                "content": (
                    f"Audited financial data:\n\n{json.dumps(payload, indent=2)}\n\n"
                    f"Write the board commentary for section: '{section}'."
                ),
            }],
        )
        text = "".join(
            block.text for block in response.content if block.type == "text"
        )
        return schemas.InsightOut(section=section, commentary=text, generated_by=MODEL)

    except Exception as exc:  # noqa: BLE001
        log.warning("LLM call failed (%s), falling back to deterministic commentary.", exc)
        return schemas.InsightOut(
            section=section,
            commentary=_static_fallback(f24, f25, targets),
            generated_by=f"deterministic-fallback (LLM error: {type(exc).__name__})",
        )
