"""
SQLAlchemy ORM models for the Senus PLC Board Report database.

Column names intentionally mirror senus_financials.json keys so seed_db.py
can unpack rows directly with **row without any mapping layer.
"""
from sqlalchemy import Column, Integer, String, Float, Boolean

from .database import Base


class Company(Base):
    """Static company metadata — one row, refreshed when fundamentals change."""

    __tablename__ = "company"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    ticker = Column(String, nullable=False)
    isin = Column(String, nullable=False)
    exchange = Column(String, nullable=False)
    listing_date = Column(String, nullable=False)
    shares_in_issue = Column(Integer, nullable=False)
    admission_share_price_eur = Column(Float, nullable=False)
    market_cap_at_listing_eur = Column(Float, nullable=False)
    sector = Column(String, nullable=False)
    employees = Column(Integer, nullable=False)


class AnnualFinancial(Base):
    """
    One row per fiscal year (FY ending 30 June).

    All monetary values in EUR. Nullable columns are those the Company has
    not disclosed or that are unavailable for a given period (e.g. customer
    breakdown only exists for FY2025+). is_preliminary flags half-year or
    unaudited periods so the UI can display appropriate caveats.
    """

    __tablename__ = "annual_financials"

    id = Column(Integer, primary_key=True, index=True)
    fiscal_year = Column(String, unique=True, index=True, nullable=False)
    period_end = Column(String, nullable=False)
    period_label = Column(String, nullable=False)          # e.g. "FY2025", "H1 FY2026"
    is_half_year = Column(Boolean, default=False)
    is_preliminary = Column(Boolean, default=False)        # unaudited / management accounts

    # Income statement
    turnover = Column(Float, nullable=True)   # nullable to support pending H1 placeholder rows
    gross_profit = Column(Float, nullable=True)
    cost_of_sales = Column(Float, nullable=True)
    gross_margin_pct = Column(Float, nullable=True)
    admin_expenses = Column(Float, nullable=True)
    rd_expense_pct_revenue = Column(Float, nullable=True)
    operating_profit_loss = Column(Float, nullable=True)
    profit_loss_before_tax = Column(Float, nullable=True)
    profit_loss_after_tax = Column(Float, nullable=True)

    # Balance sheet
    net_assets_liabilities = Column(Float, nullable=True)
    retained_earnings = Column(Float, nullable=True)
    trade_debtors = Column(Float, nullable=True)
    trade_creditors = Column(Float, nullable=True)

    # Cash flow
    cash_flow_operating = Column(Float, nullable=True)
    cash_flow_investing = Column(Float, nullable=True)
    cash_flow_financing = Column(Float, nullable=True)
    net_change_in_cash = Column(Float, nullable=True)
    cash_beginning = Column(Float, nullable=True)
    cash_end = Column(Float, nullable=True)

    # Customer KPIs
    customers_total = Column(Integer, nullable=True)
    customers_enterprise = Column(Integer, nullable=True)
    customers_independent = Column(Integer, nullable=True)
    customers_rd = Column(Integer, nullable=True)

    # Revenue mix
    revenue_channel_enterprise_pct = Column(Float, nullable=True)
    revenue_channel_independent_pct = Column(Float, nullable=True)
    revenue_channel_rd_pct = Column(Float, nullable=True)
    revenue_international_pct = Column(Float, nullable=True)
    revenue_ireland_pct = Column(Float, nullable=True)

    # Debt
    new_bank_loan_sbci = Column(Float, nullable=True)
    creditors_due_after_1yr_increase = Column(Float, nullable=True)

    # Product ACV (Enterprise tier, FY2025+)
    acv_enterprise_soil = Column(Float, nullable=True)
    acv_enterprise_terrain = Column(Float, nullable=True)
    acv_enterprise_era = Column(Float, nullable=True)

    # Additional line items first disclosed in H1 FY2026 (post-Loamin acquisition)
    other_operating_income = Column(Float, nullable=True)
    interest_payable = Column(Float, nullable=True)
    share_capital = Column(Float, nullable=True)
    share_premium = Column(Float, nullable=True)
    goodwill = Column(Float, nullable=True)
    development_costs = Column(Float, nullable=True)
    tangible_assets = Column(Float, nullable=True)
    creditors_due_within_1yr = Column(Float, nullable=True)
    contingent_consideration_loamin = Column(Float, nullable=True)

    # Commercial KPIs disclosed in H1 FY2026 narrative
    enterprise_customers_closed_in_period = Column(Integer, nullable=True)
    pipeline_value_closed_in_period_eur = Column(Float, nullable=True)
    pipeline_value_open_eur = Column(Float, nullable=True)
    equity_raised_in_period_eur = Column(Float, nullable=True)

    # Source attribution — shown in UI tooltips
    source_document = Column(String, nullable=True)
    source_section = Column(String, nullable=True)


class PostPeriodEvent(Base):
    """Material events that occurred after the balance sheet date."""

    __tablename__ = "post_period_events"

    id = Column(Integer, primary_key=True, index=True)
    date = Column(String, nullable=False)
    event = Column(String, nullable=False)
    detail = Column(String, nullable=False)
    gross_proceeds_eur = Column(Float, nullable=True)


class StrategyTarget(Base):
    """Board-stated Senus 2030 strategic targets — one row."""

    __tablename__ = "strategy_targets"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    period = Column(String, nullable=False)
    revenue_cagr_target_pct = Column(Float, nullable=False)
    revenue_cagr_base_year = Column(String, nullable=False)
    revenue_cagr_base_value = Column(Float, nullable=False)
    ebitda_positive_target_year = Column(String, nullable=False)
    enterprise_customers_target = Column(Integer, nullable=False)
    enterprise_customers_target_year = Column(String, nullable=False)
    avg_acv_target_eur = Column(Float, nullable=False)
    avg_acv_target_year = Column(String, nullable=False)
    non_ireland_revenue_target_pct = Column(Float, nullable=False)
    non_ireland_revenue_target_year = Column(String, nullable=False)
