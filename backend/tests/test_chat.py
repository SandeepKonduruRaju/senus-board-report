"""Tests for app/chat_tools.py and the /api/chat endpoint's no-key fallback."""
from app import chat_tools as ct
from app.database import SessionLocal


def _db():
    return SessionLocal()


def test_list_periods_returns_all_four():
    db = _db()
    result = ct.list_periods(db)
    labels = [p["period_label"] for p in result["periods"]]
    assert labels == ["FY2024", "H1 FY2025", "FY2025", "H1 FY2026"]
    db.close()


def test_get_annual_financials_valid_period():
    db = _db()
    result = ct.get_annual_financials(db, "FY2025")
    assert result["turnover"] == 836991
    assert result["gross_margin_pct"] == 77.5
    db.close()


def test_get_annual_financials_unknown_period_returns_error_not_exception():
    """A tool call with a bad argument should degrade gracefully — this is
    what lets the agent loop recover (e.g. by calling list_periods next)
    instead of the whole request crashing."""
    db = _db()
    result = ct.get_annual_financials(db, "NOT_A_REAL_PERIOD")
    assert "error" in result
    assert "FY2025" in result["error"]  # names a valid period as guidance
    db.close()


def test_get_disclosure_gaps_covers_all_four_flagged_metrics():
    db = _db()
    result = ct.get_disclosure_gaps(db)
    metrics = {g["metric"] for g in result["gaps"]}
    assert metrics == {"EBITDA", "ROCE", "DSCR", "Current Ratio"}
    db.close()


def test_get_company_profile():
    db = _db()
    result = ct.get_company_profile(db)
    assert result["ticker"] == "SENUS"
    db.close()


def test_get_strategy_targets():
    db = _db()
    result = ct.get_strategy_targets(db)
    assert result["revenue_cagr_target_pct"] == 50.0
    db.close()


def test_get_post_period_events_includes_h1_publication():
    db = _db()
    result = ct.get_post_period_events(db)
    events = [e["event"] for e in result["events"]]
    assert "H1 FY2026 Half Year Results published" in events
    db.close()


def test_call_tool_dispatches_correctly():
    db = _db()
    result = ct.call_tool(db, "get_company_profile", {})
    assert result["ticker"] == "SENUS"
    db.close()


def test_call_tool_unknown_name_returns_error_not_exception():
    db = _db()
    result = ct.call_tool(db, "definitely_not_a_tool", {})
    assert "error" in result
    db.close()


def test_call_tool_passes_arguments_through():
    db = _db()
    result = ct.call_tool(db, "get_annual_financials", {"fiscal_year": "H1_FY2026"})
    assert result["turnover"] == 354813
    db.close()


# ---------------------------------------------------------------------------
# /api/chat endpoint — keyword fallback (no API key required to test)
# ---------------------------------------------------------------------------

def test_chat_endpoint_revenue_fallback(client, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    r = client.post("/api/chat", json={"message": "What was our revenue in FY2025?"})
    assert r.status_code == 200
    body = r.json()
    assert "836,991" in body["answer"]
    assert body["generated_by"] == "keyword-fallback"


def test_chat_endpoint_ebitda_fallback(client, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    r = client.post("/api/chat", json={"message": "why no ebitda?"})
    assert r.status_code == 200
    assert "D&A" in r.json()["answer"]


def test_chat_endpoint_unmatched_question_without_key_returns_503(client, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    r = client.post("/api/chat", json={"message": "what's your favourite colour?"})
    assert r.status_code == 503
    assert "ANTHROPIC_API_KEY" in r.json()["detail"]


def test_chat_endpoint_requires_message_field(client):
    r = client.post("/api/chat", json={})
    assert r.status_code == 422  # Pydantic validation error, not a 500
