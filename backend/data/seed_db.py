"""Seeds the SQLite database from senus_financials.json.

Run with:  python -m data.seed_db
(run from the backend/ directory so the app package resolves)
"""
import json
from pathlib import Path

from app.database import Base, engine, SessionLocal
from app.models import Company, AnnualFinancial, StrategyTarget, PostPeriodEvent

DATA_FILE = Path(__file__).parent / "senus_financials.json"


def seed():
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)

    data = json.loads(DATA_FILE.read_text())
    db = SessionLocal()
    try:
        c = data["company"]
        company = Company(
            name=c["name"],
            ticker=c["ticker"],
            isin=c["isin"],
            exchange=c["exchange"],
            listing_date=c["listing_date"],
            shares_in_issue=c["shares_in_issue"],
            admission_share_price_eur=c["admission_share_price_eur"],
            market_cap_at_listing_eur=c["market_cap_at_listing_eur"],
            sector=c["sector"],
            employees=c["employees"],
        )
        db.add(company)

        for row in data["annual_financials"]:
            db.add(AnnualFinancial(**row))

        for ev in data["post_period_events"]:
            db.add(PostPeriodEvent(
                date=ev["date"], event=ev["event"], detail=ev["detail"],
                gross_proceeds_eur=ev.get("gross_proceeds_eur"),
            ))

        st = data["strategy_targets"]
        db.add(StrategyTarget(**st))

        db.commit()
        print(f"Seeded database at {engine.url} with "
              f"{len(data['annual_financials'])} annual financial records.")
    finally:
        db.close()


if __name__ == "__main__":
    seed()
