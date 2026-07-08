"""Tests for /api/insights — the AI board commentary endpoint."""
import os


def test_insights_falls_back_without_api_key(client, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    r = client.get("/api/insights?section=overview")
    assert r.status_code == 200
    body = r.json()
    assert "deterministic-fallback" in body["generated_by"]
    assert len(body["commentary"]) > 0


def test_insights_fallback_cites_real_figures(client, monkeypatch):
    """The deterministic fallback should quote actual revenue/margin figures
    from the seeded data, not placeholder text."""
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    r = client.get("/api/insights?section=overview")
    commentary = r.json()["commentary"]
    assert "836,991" in commentary  # FY2025 revenue
    assert "21.6%" in commentary    # FY24->FY25 growth


def test_insights_accepts_any_section_name(client, monkeypatch):
    monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
    for section in ["overview", "growth", "profitability", "cash", "solvency", "returns"]:
        r = client.get(f"/api/insights?section={section}")
        assert r.status_code == 200
        assert r.json()["section"] == section
