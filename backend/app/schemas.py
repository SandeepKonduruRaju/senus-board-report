"""
Pydantic v2 response schemas — the public API contract.

Kept separate from ORM models so internal DB changes don't automatically
become breaking API changes.
"""
from typing import Optional
from pydantic import BaseModel, Field


class AnnualFinancialOut(BaseModel):
    fiscal_year: str
    period_end: str
    # Income statement
    turnover: float
    gross_profit: float
    cost_of_sales: Optional[float] = None
    gross_margin_pct: float
    admin_expenses: float
    rd_expense_pct_revenue: Optional[float] = None
    operating_profit_loss: float
    profit_loss_before_tax: float
    profit_loss_after_tax: float
    # Balance sheet
    net_assets_liabilities: float
    retained_earnings: float
    trade_debtors: Optional[float] = None
    trade_creditors: Optional[float] = None
    # Cash flow
    cash_flow_operating: float
    cash_flow_investing: float
    cash_flow_financing: float
    net_change_in_cash: Optional[float] = None
    cash_beginning: Optional[float] = None
    cash_end: float
    # Customer KPIs
    customers_total: Optional[int] = None
    customers_enterprise: Optional[int] = None
    customers_independent: Optional[int] = None
    customers_rd: Optional[int] = None
    # Revenue mix
    revenue_channel_enterprise_pct: Optional[float] = None
    revenue_channel_independent_pct: Optional[float] = None
    revenue_channel_rd_pct: Optional[float] = None
    revenue_international_pct: Optional[float] = None
    revenue_ireland_pct: Optional[float] = None
    # Product ACV
    acv_enterprise_soil: Optional[float] = None
    acv_enterprise_terrain: Optional[float] = None
    acv_enterprise_era: Optional[float] = None

    model_config = {"from_attributes": True}


class CompanyOut(BaseModel):
    name: str
    ticker: str
    isin: str
    exchange: str
    listing_date: str
    shares_in_issue: int
    admission_share_price_eur: float
    market_cap_at_listing_eur: float
    sector: str
    employees: int

    model_config = {"from_attributes": True}


class KpiOut(BaseModel):
    label: str
    fy2024: Optional[float] = None
    fy2025: Optional[float] = None
    yoy_change_pct: Optional[float] = None
    unit: str
    note: Optional[str] = Field(
        default=None,
        description="Disclosure caveat or methodology note shown as a tooltip in the UI"
    )
    source: str = Field(
        default="Senus PLC Information Document, Dec 2025 (Euronext Access Direct Listing)",
        description="Audit-trail source reference shown on hover in the dashboard"
    )


class ProFormaRunwayOut(BaseModel):
    fy2025_cash_end: float
    placement_gross_proceeds: Optional[float]
    pro_forma_cash: float
    fy2025_avg_monthly_burn: float
    pro_forma_runway_months: float
    note: str
    source: str = "Senus PLC Information Document, Dec 2025 + Private Placement announcement"


class InsightOut(BaseModel):
    section: str
    commentary: str
    generated_by: str
