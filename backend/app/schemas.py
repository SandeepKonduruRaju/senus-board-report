"""
Pydantic v2 response schemas.

These are the public API contracts — independent of the ORM layer so that
internal database changes don't automatically become breaking API changes.
"""
from typing import Optional

from pydantic import BaseModel, Field


class AnnualFinancialOut(BaseModel):
    fiscal_year: str
    period_end: str
    period_label: str
    is_half_year: bool = False
    is_preliminary: bool = False

    # Income statement
    turnover: float
    gross_profit: Optional[float] = None
    cost_of_sales: Optional[float] = None
    gross_margin_pct: Optional[float] = None
    admin_expenses: Optional[float] = None
    rd_expense_pct_revenue: Optional[float] = None
    operating_profit_loss: Optional[float] = None
    profit_loss_before_tax: Optional[float] = None
    profit_loss_after_tax: Optional[float] = None

    # Balance sheet
    net_assets_liabilities: Optional[float] = None
    retained_earnings: Optional[float] = None
    trade_debtors: Optional[float] = None
    trade_creditors: Optional[float] = None

    # Cash flow
    cash_flow_operating: Optional[float] = None
    cash_flow_investing: Optional[float] = None
    cash_flow_financing: Optional[float] = None
    net_change_in_cash: Optional[float] = None
    cash_beginning: Optional[float] = None
    cash_end: Optional[float] = None

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

    # H1 FY2026-onward line items
    other_operating_income: Optional[float] = None
    interest_payable: Optional[float] = None
    share_capital: Optional[float] = None
    share_premium: Optional[float] = None
    goodwill: Optional[float] = None
    development_costs: Optional[float] = None
    tangible_assets: Optional[float] = None
    creditors_due_within_1yr: Optional[float] = None
    contingent_consideration_loamin: Optional[float] = None
    enterprise_customers_closed_in_period: Optional[int] = None
    pipeline_value_closed_in_period_eur: Optional[float] = None
    pipeline_value_open_eur: Optional[float] = None
    equity_raised_in_period_eur: Optional[float] = None

    # Source attribution (for UI tooltips)
    source_document: Optional[str] = None
    source_section: Optional[str] = None

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
    h1_fy2026: Optional[float] = Field(default=None, description="H1 FY2026 if available")
    yoy_change_pct: Optional[float] = None
    unit: str
    source: Optional[str] = Field(default=None, description="Source document and section for UI tooltip")
    note: Optional[str] = Field(default=None, description="Disclosure caveat or methodology note")


class ProFormaRunwayOut(BaseModel):
    fy2025_cash_end: float
    placement_gross_proceeds: Optional[float]
    pro_forma_cash: float
    fy2025_avg_monthly_burn: float
    pro_forma_runway_months: float
    note: str


class InsightOut(BaseModel):
    section: str
    commentary: str
    generated_by: str
