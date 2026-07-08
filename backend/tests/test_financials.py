"""Tests for /api/financials/* endpoints."""


def test_health(client):
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json() == {"status": "healthy"}


def test_company_returns_senus(client):
    r = client.get("/api/financials/company")
    assert r.status_code == 200
    body = r.json()
    assert body["ticker"] == "SENUS"
    assert body["isin"] == "IE000O0F49R3"


def test_annual_returns_four_real_periods(client):
    """Regression guard: the platform should show FY2024, H1 FY2025, FY2025,
    H1 FY2026 — not the two-period placeholder from the initial build."""
    r = client.get("/api/financials/annual")
    assert r.status_code == 200
    labels = [row["period_label"] for row in r.json()]
    assert labels == ["FY2024", "H1 FY2025", "FY2025", "H1 FY2026"]


def test_annual_figures_match_audited_source(client):
    """Spot-check figures against the Information Document / Half Year Results
    — the numbers that matter most if this platform is ever challenged on
    accuracy in an interview."""
    rows = {r["period_label"]: r for r in client.get("/api/financials/annual").json()}

    assert rows["FY2025"]["turnover"] == 836991
    assert rows["FY2025"]["gross_margin_pct"] == 77.5
    assert rows["FY2025"]["customers_total"] == 138

    assert rows["H1 FY2026"]["turnover"] == 354813
    assert rows["H1 FY2026"]["cash_end"] == 735189


def test_kpis_yoy_calculation(client):
    r = client.get("/api/financials/kpis")
    kpis = {k["label"]: k for k in r.json()}

    revenue = kpis["Revenue"]
    assert revenue["fy2024"] == 688317
    assert revenue["fy2025"] == 836991
    # (836991 - 688317) / 688317 * 100, rounded to 1dp
    assert revenue["yoy_change_pct"] == 21.6


def test_kpis_include_h1_fy2026_revenue(client):
    r = client.get("/api/financials/kpis")
    revenue = next(k for k in r.json() if k["label"] == "Revenue")
    assert revenue["h1_fy2026"] == 354813


def test_kpis_every_entry_has_a_source(client):
    """Every KPI should be traceable — this is the 'stand over the outputs'
    requirement enforced as a test, not just a UI convention."""
    r = client.get("/api/financials/kpis")
    for kpi in r.json():
        assert kpi.get("source"), f"KPI '{kpi['label']}' is missing a source"


def test_pro_forma_runway_shows_estimate_and_actual(client):
    r = client.get("/api/financials/pro-forma-runway")
    body = r.json()

    assert body["illustrative_estimate"]["estimated_runway_months"] > 0
    assert body["actual_h1_fy2026"] is not None
    assert body["actual_h1_fy2026"]["cash_end"] == 735189
    # The actual outcome should differ from the naive estimate — that's the point.
    assert body["actual_h1_fy2026"]["variance_vs_illustrative_cash"] != 0


def test_strategy_targets(client):
    r = client.get("/api/financials/strategy-targets")
    assert r.status_code == 200
    assert r.json()["revenue_cagr_target_pct"] == 50.0


def test_post_period_events_includes_h1_publication(client):
    r = client.get("/api/financials/post-period-events")
    events = [e["event"] for e in r.json()]
    assert "H1 FY2026 Half Year Results published" in events
