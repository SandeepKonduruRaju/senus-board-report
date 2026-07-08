"""Tests for data/extract_financials.py's validation logic.

These don't call the live Anthropic API (no key needed to run this suite) —
they test the sanity_check() guardrail that would catch an implausible
extraction before it ever reached the database.
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from data.extract_financials import sanity_check  # noqa: E402


def test_sanity_check_passes_valid_record():
    """This is Senus's real FY2025 data: PAT is less negative than PBT
    because of a small tax credit — legitimate, should not be flagged."""
    record = {
        "fiscal_year": "FY2025",
        "turnover": 836991,
        "gross_profit": 648450,
        "profit_loss_before_tax": -635768,
        "profit_loss_after_tax": -590256,
    }
    assert sanity_check(record) == []


def test_sanity_check_flags_gross_profit_exceeding_turnover():
    record = {"fiscal_year": "FY2025", "turnover": 100, "gross_profit": 150}
    issues = sanity_check(record)
    assert len(issues) == 1
    assert "exceeds turnover" in issues[0]


def test_sanity_check_flags_implausibly_large_tax_adjustment():
    """A tax adjustment larger than 50% of PBT is unusual enough to flag for
    human review — this is the genuinely suspicious case, unlike a normal
    small tax credit (see test_sanity_check_passes_valid_record)."""
    record = {
        "fiscal_year": "FY2025",
        "profit_loss_before_tax": -100,
        "profit_loss_after_tax": 50,  # tax adjustment of +150, i.e. 150% of PBT
    }
    issues = sanity_check(record)
    assert len(issues) == 1
    assert "tax adjustment" in issues[0]


def test_sanity_check_handles_missing_fields_gracefully():
    """A record extracted from a document that simply doesn't disclose
    every field should not crash the pipeline."""
    assert sanity_check({"fiscal_year": "FY2025"}) == []
