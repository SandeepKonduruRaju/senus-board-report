from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from .. import models, schemas
from ..database import get_db

router = APIRouter(prefix="/api/financials", tags=["financials"])


def yoy(a, b):
    """% change from a (older) to b (newer). Returns None if a is 0/None."""
    if a in (None, 0) or b is None:
        return None
    return round(((b - a) / abs(a)) * 100, 1)


@router.get("/company", response_model=schemas.CompanyOut)
def get_company(db: Session = Depends(get_db)):
    return db.query(models.Company).first()


@router.get("/annual", response_model=list[schemas.AnnualFinancialOut])
def get_annual(db: Session = Depends(get_db)):
    return db.query(models.AnnualFinancial).order_by(models.AnnualFinancial.fiscal_year).all()


@router.get("/kpis", response_model=list[schemas.KpiOut])
def get_kpis(db: Session = Depends(get_db)):
    """Computed board-level KPIs, FY2024 vs FY2025, with explicit unit/notes.

    Metrics that cannot be reliably computed from disclosed figures
    (EBITDA, current ratio, DSCR, ROCE where capital employed is ~0) are
    deliberately omitted or flagged rather than estimated silently — see
    disclosure_gaps in senus_financials.json / the README.
    """
    rows = {r.fiscal_year: r for r in db.query(models.AnnualFinancial).all()}
    f24, f25 = rows.get("FY2024"), rows.get("FY2025")

    kpis = [
        schemas.KpiOut(
            label="Revenue", fy2024=f24.turnover, fy2025=f25.turnover,
            yoy_change_pct=yoy(f24.turnover, f25.turnover), unit="EUR",
        ),
        schemas.KpiOut(
            label="Gross Margin", fy2024=f24.gross_margin_pct, fy2025=f25.gross_margin_pct,
            yoy_change_pct=round(f25.gross_margin_pct - f24.gross_margin_pct, 1), unit="pp",
            note="Percentage-point change shown, not YoY %.",
        ),
        schemas.KpiOut(
            label="Operating Loss", fy2024=f24.operating_profit_loss, fy2025=f25.operating_profit_loss,
            yoy_change_pct=yoy(f24.operating_profit_loss, f25.operating_profit_loss), unit="EUR",
            note="Operating Margin proxy — EBITDA not separately disclosed (D&A not broken out).",
        ),
        schemas.KpiOut(
            label="Net Loss After Tax", fy2024=f24.profit_loss_after_tax, fy2025=f25.profit_loss_after_tax,
            yoy_change_pct=yoy(f24.profit_loss_after_tax, f25.profit_loss_after_tax), unit="EUR",
        ),
        schemas.KpiOut(
            label="Cash & Cash Equivalents (period end)", fy2024=f24.cash_end, fy2025=f25.cash_end,
            yoy_change_pct=yoy(f24.cash_end, f25.cash_end), unit="EUR",
        ),
        schemas.KpiOut(
            label="Net Cash Used in Operations", fy2024=f24.cash_flow_operating, fy2025=f25.cash_flow_operating,
            yoy_change_pct=yoy(f24.cash_flow_operating, f25.cash_flow_operating), unit="EUR",
        ),
        schemas.KpiOut(
            label="Net Assets / (Liabilities)", fy2024=f24.net_assets_liabilities, fy2025=f25.net_assets_liabilities,
            yoy_change_pct=None, unit="EUR",
            note="FY2025 closed with net liabilities; ROCE is not meaningful (denominator ~0/negative) and is omitted rather than shown misleadingly.",
        ),
        schemas.KpiOut(
            label="Cash Runway (book, FYE, pre-placement)",
            fy2024=round(f24.cash_end / (abs(f24.cash_flow_operating) / 12), 1) if f24.cash_flow_operating else None,
            fy2025=round(f25.cash_end / (abs(f25.cash_flow_operating) / 12), 1) if f25.cash_flow_operating else None,
            yoy_change_pct=None, unit="months",
            note="Cash at year-end / average monthly operating cash burn for that year. Does not include the Dec-2025 EUR 1.1m placement — see pro-forma runway.",
        ),
    ]
    return kpis


@router.get("/pro-forma-runway")
def pro_forma_runway(db: Session = Depends(get_db)):
    """Illustrative pro-forma cash runway including the Dec 2025 Private Placement.
    Clearly labelled as pro-forma / estimated, not a disclosed figure."""
    f25 = db.query(models.AnnualFinancial).filter_by(fiscal_year="FY2025").first()
    placement = db.query(models.PostPeriodEvent).filter(
        models.PostPeriodEvent.event == "2025 Private Placement completed"
    ).first()
    monthly_burn = abs(f25.cash_flow_operating) / 12
    pro_forma_cash = f25.cash_end + (placement.gross_proceeds_eur if placement else 0)
    return {
        "fy2025_cash_end": f25.cash_end,
        "placement_gross_proceeds": placement.gross_proceeds_eur if placement else None,
        "pro_forma_cash": pro_forma_cash,
        "fy2025_avg_monthly_burn": round(monthly_burn, 0),
        "pro_forma_runway_months": round(pro_forma_cash / monthly_burn, 1),
        "note": (
            "Illustrative only: assumes FY2025 burn rate continues, gross (not net-of-fees) "
            "placement proceeds, and no change in the cost base — all of which the Board's own "
            "growth investment plans make unlikely in practice. Directors state the Company is "
            "'well capitalised... through the next two financial years ending 30 June 2027', "
            "which this estimate is broadly consistent with."
        ),
    }


@router.get("/strategy-targets")
def strategy_targets(db: Session = Depends(get_db)):
    return db.query(models.StrategyTarget).first()


@router.get("/post-period-events")
def post_period_events(db: Session = Depends(get_db)):
    return db.query(models.PostPeriodEvent).all()
