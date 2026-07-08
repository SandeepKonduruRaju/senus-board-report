"""
Financials router — serves raw and derived financial metrics.

All endpoints are read-only (GET). Metrics that cannot be reliably computed
from disclosed figures are explicitly omitted and noted, never estimated.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/financials", tags=["financials"])

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

SOURCE_INFO_DOC = "Senus PLC Information Document, Dec 2025, Section 7.1"
SOURCE_H1 = "Senus PLC H1 FY2026 Interim Results, Mar 2026"
PLACEMENT_EVENT_NAME = "2025 Private Placement completed"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _yoy(a: Optional[float], b: Optional[float]) -> Optional[float]:
    """Percentage change from a (older) to b (newer). None if either is 0/None."""
    if not a or b is None:
        return None
    return round(((b - a) / abs(a)) * 100, 1)


def _get_period(db: Session, fiscal_year: str) -> models.AnnualFinancial:
    row = db.query(models.AnnualFinancial).filter_by(fiscal_year=fiscal_year).first()
    if row is None:
        raise HTTPException(status_code=404, detail=f"Period {fiscal_year!r} not found")
    return row


# ---------------------------------------------------------------------------
# Endpoints
# ---------------------------------------------------------------------------

@router.get("/company", response_model=schemas.CompanyOut, summary="Company metadata")
def get_company(db: Session = Depends(get_db)) -> models.Company:
    company = db.query(models.Company).first()
    if company is None:
        raise HTTPException(status_code=404, detail="Company record not found — run seed_db.py")
    return company


@router.get(
    "/annual",
    response_model=list[schemas.AnnualFinancialOut],
    summary="All annual financial periods",
)
def get_annual(db: Session = Depends(get_db)) -> list[models.AnnualFinancial]:
    """Returns all periods in chronological order, including H1 placeholder rows."""
    return (
        db.query(models.AnnualFinancial)
        .order_by(models.AnnualFinancial.period_end)
        .all()
    )


@router.get(
    "/kpis",
    response_model=list[schemas.KpiOut],
    summary="Computed board-level KPIs",
)
def get_kpis(db: Session = Depends(get_db)) -> list[schemas.KpiOut]:
    """
    Derived KPIs across disclosed periods.

    Metrics that cannot be reliably computed (EBITDA, Current Ratio, DSCR,
    ROCE where capital employed is ~0) are deliberately omitted — see
    disclosure_gaps in senus_financials.json and the README.
    """
    f24 = _get_period(db, "FY2024")
    f25 = _get_period(db, "FY2025")
    h1_25 = db.query(models.AnnualFinancial).filter_by(fiscal_year="H1_FY2025").first()
    h1_26 = db.query(models.AnnualFinancial).filter_by(fiscal_year="H1_FY2026").first()

    h1_revenue = h1_26.turnover if h1_26 else None
    h1_margin = h1_26.gross_margin_pct if h1_26 else None
    h1_yoy = _yoy(h1_25.turnover, h1_26.turnover) if (h1_25 and h1_26) else None

    return [
        schemas.KpiOut(
            label="Revenue",
            fy2024=f24.turnover,
            fy2025=f25.turnover,
            h1_fy2026=h1_revenue,
            yoy_change_pct=_yoy(f24.turnover, f25.turnover),
            unit="EUR",
            source=SOURCE_INFO_DOC,
            note=(
                f"H1 FY2026 revenue €{h1_revenue:,.0f}, up {h1_yoy}% vs H1 FY2025 (unaudited)."
                if h1_revenue and h1_yoy is not None else None
            ),
        ),
        schemas.KpiOut(
            label="Gross Margin",
            fy2024=f24.gross_margin_pct,
            fy2025=f25.gross_margin_pct,
            h1_fy2026=h1_margin,
            yoy_change_pct=round(f25.gross_margin_pct - f24.gross_margin_pct, 1),
            unit="pp",
            source=SOURCE_INFO_DOC,
            note="Percentage-point change shown, not YoY %.",
        ),
        schemas.KpiOut(
            label="Operating Loss",
            fy2024=f24.operating_profit_loss,
            fy2025=f25.operating_profit_loss,
            yoy_change_pct=_yoy(f24.operating_profit_loss, f25.operating_profit_loss),
            unit="EUR",
            source=SOURCE_INFO_DOC,
            note="EBITDA proxy — D&A not separately disclosed so EBITDA cannot be computed.",
        ),
        schemas.KpiOut(
            label="Net Loss After Tax",
            fy2024=f24.profit_loss_after_tax,
            fy2025=f25.profit_loss_after_tax,
            yoy_change_pct=_yoy(f24.profit_loss_after_tax, f25.profit_loss_after_tax),
            unit="EUR",
            source=SOURCE_INFO_DOC,
        ),
        schemas.KpiOut(
            label="Cash & Cash Equivalents",
            fy2024=f24.cash_end,
            fy2025=f25.cash_end,
            yoy_change_pct=_yoy(f24.cash_end, f25.cash_end),
            unit="EUR",
            source=SOURCE_INFO_DOC,
            note=(
                "Period-end balance. Dec-2025 placement (€1.1m gross) is "
                "post-period — see pro-forma runway."
            ),
        ),
        schemas.KpiOut(
            label="Net Cash Used in Operations",
            fy2024=f24.cash_flow_operating,
            fy2025=f25.cash_flow_operating,
            yoy_change_pct=_yoy(f24.cash_flow_operating, f25.cash_flow_operating),
            unit="EUR",
            source=SOURCE_INFO_DOC,
        ),
        schemas.KpiOut(
            label="Net Assets / (Liabilities)",
            fy2024=f24.net_assets_liabilities,
            fy2025=f25.net_assets_liabilities,
            unit="EUR",
            source=SOURCE_INFO_DOC,
            note="FY2025 closed with net liabilities. ROCE omitted — capital employed near zero/negative.",
        ),
        schemas.KpiOut(
            label="Cash Runway (pre-placement)",
            fy2024=round(f24.cash_end / (abs(f24.cash_flow_operating) / 12), 1),
            fy2025=round(f25.cash_end / (abs(f25.cash_flow_operating) / 12), 1),
            unit="months",
            source=SOURCE_INFO_DOC,
            note="Cash at FYE ÷ avg monthly operating burn. Excludes Dec-2025 placement proceeds.",
        ),
    ]


@router.get(
    "/pro-forma-runway",
    summary="Illustrative pro-forma runway vs actual H1 FY2026 outcome",
    response_model=None,
)
def pro_forma_runway(db: Session = Depends(get_db)) -> dict:
    """
    Two numbers, deliberately shown side by side:

    1. The illustrative pro-forma estimate a Board would have made at FY2025
       year-end, before H1 FY2026 results existed (gross placement proceeds
       added to FY2025 closing cash, FY2025 burn rate assumed to continue).
    2. The actual reported H1 FY2026 outcome (Half Year Results, 19 Mar 2026),
       which came in higher than the naive pro-forma — driven by the
       Loamin-related financing inflows and working capital timing that a
       simple pro-forma can't capture.

    Showing both, rather than only the actual figure, demonstrates why
    illustrative estimates should be labelled and revisited against real
    outcomes rather than treated as forecasts.
    """
    f25 = _get_period(db, "FY2025")
    h1_26 = db.query(models.AnnualFinancial).filter_by(fiscal_year="H1_FY2026").first()
    placement = db.query(models.PostPeriodEvent).filter_by(
        event=PLACEMENT_EVENT_NAME
    ).first()

    monthly_burn_fy25 = abs(f25.cash_flow_operating) / 12
    proceeds = placement.gross_proceeds_eur if placement else 0.0
    illustrative_pro_forma_cash = f25.cash_end + proceeds
    illustrative_runway_months = round(illustrative_pro_forma_cash / monthly_burn_fy25, 1)

    result = {
        "illustrative_estimate": {
            "basis": "FY2025 cash + gross placement proceeds, FY2025 burn rate assumed",
            "fy2025_cash_end": f25.cash_end,
            "placement_gross_proceeds": proceeds or None,
            "estimated_cash": illustrative_pro_forma_cash,
            "estimated_monthly_burn": round(monthly_burn_fy25, 0),
            "estimated_runway_months": illustrative_runway_months,
        },
        "actual_h1_fy2026": None,
        "note": (
            "Illustrative estimate assumes FY2025 burn rate continues and uses gross "
            "(not net-of-fees) proceeds. Compare against actual_h1_fy2026 below, now "
            "that H1 FY2026 results (19 Mar 2026) are available."
        ),
    }

    if h1_26 and h1_26.cash_end is not None:
        h1_monthly_burn = abs(h1_26.cash_flow_operating) / 6
        result["actual_h1_fy2026"] = {
            "basis": "Reported Half Year Results, 6 months to 31 Dec 2025 (unaudited)",
            "cash_end": h1_26.cash_end,
            "monthly_burn": round(h1_monthly_burn, 0),
            "runway_months_from_period_end": round(h1_26.cash_end / h1_monthly_burn, 1),
            "variance_vs_illustrative_cash": round(h1_26.cash_end - illustrative_pro_forma_cash, 0),
            "variance_explanation": (
                "Actual cash came in lower than the illustrative estimate, despite the "
                "equity raise landing in-period (€1.14m recognised in H1 FY2026 financing "
                "activities, slightly above the €1.1m gross placement figure). The gap is "
                "explained by (1) operating burn running well above the FY2025 rate used "
                "in the estimate — roughly €68k/month vs ~€31k/month — as Loamin "
                "integration costs came onto the P&L, and (2) a €124,837 loan repayment "
                "in financing activities that the illustrative estimate did not anticipate. "
                "Net effect: runway is still reasonable (~11 months from the H1 cash "
                "position alone, before any further fundraising) but for materially "
                "different reasons than the original estimate assumed — precisely why "
                "illustrative estimates need to be revisited against actuals, not treated "
                "as forecasts."
            ),
        }

    return result


@router.get("/strategy-targets", summary="Senus 2030 strategic targets", response_model=None)
def strategy_targets(db: Session = Depends(get_db)) -> dict:
    target = db.query(models.StrategyTarget).first()
    if target is None:
        raise HTTPException(status_code=404, detail="No strategy targets found — run seed_db.py")
    return {c.name: getattr(target, c.name) for c in target.__table__.columns}


@router.get("/post-period-events", summary="Material post-period events", response_model=None)
def post_period_events(db: Session = Depends(get_db)) -> list[dict]:
    rows = db.query(models.PostPeriodEvent).order_by(models.PostPeriodEvent.date).all()
    return [{c.name: getattr(r, c.name) for c in r.__table__.columns} for r in rows]
