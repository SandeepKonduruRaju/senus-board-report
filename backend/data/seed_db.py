"""
Loads senus_financials.json into the application database.

Run from the backend/ directory:
    python -m data.seed_db

Safe to re-run — drops and recreates all tables each time.
"""
import json
import logging
from pathlib import Path

from app.database import Base, engine, SessionLocal
from app.models import (
    Company, AnnualFinancial, StrategyTarget, PostPeriodEvent,
)

logging.basicConfig(level=logging.INFO, format="%(message)s")
log = logging.getLogger(__name__)

DATA_FILE = Path(__file__).parent / "senus_financials.json"

# Keys present in the JSON that are NOT columns in AnnualFinancial
# (e.g. comments, helper fields). Stripped before **unpacking into the model.
_ANNUAL_EXCLUDE = {"_comment"}


def _load_annual(row: dict) -> AnnualFinancial:
    """Strip non-column keys and instantiate an AnnualFinancial row."""
    clean = {k: v for k, v in row.items() if k not in _ANNUAL_EXCLUDE}
    return AnnualFinancial(**clean)


def seed() -> None:
    log.info("Dropping and recreating all tables...")
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    data = json.loads(DATA_FILE.read_text())
    db = SessionLocal()

    try:
        # Company
        c = data["company"]
        db.add(Company(
            name=c["name"], ticker=c["ticker"], isin=c["isin"],
            exchange=c["exchange"], listing_date=c["listing_date"],
            shares_in_issue=c["shares_in_issue"],
            admission_share_price_eur=c["admission_share_price_eur"],
            market_cap_at_listing_eur=c["market_cap_at_listing_eur"],
            sector=c["sector"], employees=c["employees"],
        ))
        log.info("  ✓ Company")

        # Annual financials (including H1 placeholder rows)
        for row in data["annual_financials"]:
            db.add(_load_annual(row))
        log.info(f"  ✓ {len(data['annual_financials'])} annual financial rows")

        # Post-period events
        for ev in data["post_period_events"]:
            db.add(PostPeriodEvent(
                date=ev["date"],
                event=ev["event"],
                detail=ev["detail"],
                gross_proceeds_eur=ev.get("gross_proceeds_eur"),
            ))
        log.info(f"  ✓ {len(data['post_period_events'])} post-period events")

        # Strategy targets
        db.add(StrategyTarget(**data["strategy_targets"]))
        log.info("  ✓ Strategy targets")

        db.commit()
        log.info(f"\nDatabase seeded at: {engine.url}")

    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    seed()
