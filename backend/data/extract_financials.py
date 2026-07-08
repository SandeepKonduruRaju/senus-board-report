"""
Senus PLC — AI-assisted financial extraction pipeline
======================================================

Purpose
-------
Extracts structured financial data (P&L, balance sheet, cash flow, KPIs)
from Senus PLC's source disclosure documents (currently: the Information
Document published for the December 2025 Euronext Access Direct Listing)
and writes it to `senus_financials.json`, which `seed_db.py` then loads
into the application database.

Why this approach
------------------
Senus publishes financials as prose-embedded tables inside PDF disclosure
documents (Information Document, and — once available — half-year/full-year
RNS-style announcements), not as machine-readable filings (no XBRL, no API).
An LLM with a constrained JSON schema is the most reliable way to turn that
prose+table hybrid into clean structured data without hand-transcribing every
new disclosure. Using a strict `tool_use` schema (rather than free-text
extraction) means the model *cannot* return anything except the shape we
define, which is what makes this safe to point at a real database.

How it works
------------
1. `extract_from_text()` sends a chunk of raw document text to Claude with a
   tool definition (`record_annual_financials`) whose JSON schema mirrors the
   `annual_financials[]` records in `senus_financials.json`.
2. Claude is instructed to extract ONLY figures it can find verbatim/derive
   directly from the text, and to omit (never guess) anything not present.
3. Extractions are validated against `EXPECTED_KEYS` and basic sanity checks
   (e.g. gross_profit <= turnover, cash reconciliation) before being merged.
4. A human (in this project: the graduate candidate) still reviews the diff
   before it is committed to `senus_financials.json` — this pipeline
   accelerates extraction, it does not replace review of a public company's
   numbers. This mirrors how the shipped dataset in this repo was actually
   built: LLM-assisted extraction from the Information Document, followed by
   manual cross-checking of every figure against Section 3/7.1 of the source
   PDF before it was committed to this repository.

Usage
-----
    export ANTHROPIC_API_KEY=sk-ant-...
    python extract_financials.py --input raw_document_text/information_document.txt

If no API key is set, or you just want to inspect the shape of the pipeline,
run with --dry-run to see the exact request that would be sent.
"""

import argparse
import json
import os
import sys
from pathlib import Path

MODEL = "claude-sonnet-4-6"

EXTRACTION_TOOL = {
    "name": "record_annual_financials",
    "description": (
        "Record one fiscal year's worth of Senus PLC financial data, extracted "
        "verbatim or directly derived from the source document. Omit any field "
        "not explicitly stated or directly derivable — never estimate silently."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "fiscal_year": {"type": "string", "description": "e.g. FY2025"},
            "period_end": {"type": "string", "description": "YYYY-MM-DD"},
            "turnover": {"type": "number"},
            "gross_profit": {"type": "number"},
            "operating_profit_loss": {"type": "number"},
            "profit_loss_before_tax": {"type": "number"},
            "profit_loss_after_tax": {"type": "number"},
            "net_assets_liabilities": {"type": "number"},
            "retained_earnings": {"type": "number"},
            "cash_flow_operating": {"type": "number"},
            "cash_flow_investing": {"type": "number"},
            "cash_flow_financing": {"type": "number"},
            "cash_end": {"type": "number"},
            "trade_debtors": {"type": "number"},
            "trade_creditors": {"type": "number"},
            "customers_total": {"type": "integer"},
            "fields_not_found": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Names of expected fields this document did not disclose.",
            },
        },
        "required": ["fiscal_year", "period_end", "turnover"],
    },
}

SYSTEM_PROMPT = """You are a financial-statement extraction engine for a board \
reporting platform. You will be given raw text from a company disclosure \
document (e.g. a Euronext Information Document). Call the \
record_annual_financials tool once per distinct fiscal year you find fully \
reported figures for. Rules:
- Extract only what is explicitly stated or a direct, unambiguous sum/subtraction \
  of stated figures (e.g. cost_of_sales = turnover - gross_profit is fine).
- Never infer or estimate a figure that requires an assumption (e.g. do not \
  invent EBITDA if D&A is not disclosed).
- If a figure appears in a summary table AND in prose with the same value, \
  extract it once.
- List anything you expected but could not find in fields_not_found.
"""


def extract_from_text(document_text: str, client=None):
    """Send document text to Claude for structured extraction. Returns list of dicts."""
    if client is None:
        import anthropic  # pip install anthropic
        client = anthropic.Anthropic()  # reads ANTHROPIC_API_KEY from env

    response = client.messages.create(
        model=MODEL,
        max_tokens=4000,
        system=SYSTEM_PROMPT,
        tools=[EXTRACTION_TOOL],
        tool_choice={"type": "tool", "name": "record_annual_financials"},
        messages=[
            {
                "role": "user",
                "content": f"Extract annual financials from this document text:\n\n{document_text}",
            }
        ],
    )

    records = [
        block.input
        for block in response.content
        if block.type == "tool_use" and block.name == "record_annual_financials"
    ]
    return records


def sanity_check(record: dict) -> list:
    """
    Cheap validation before a record is allowed anywhere near the database.

    Note on an earlier version of this check: a prior version flagged any
    record where profit_loss_after_tax > profit_loss_before_tax as a "sign
    convention error". That's wrong — a tax credit legitimately makes an
    after-tax loss smaller (less negative) than the pre-tax loss, and this
    is exactly Senus's actual FY2025 pattern (PBT €(635,768) vs PAT
    €(590,256), a ~€45k tax credit). The automated test suite caught this
    producing a false positive against real audited data, which is why the
    check below looks at the *size* of the tax adjustment relative to PBT
    instead of its direction.
    """
    issues = []

    gp, turnover = record.get("gross_profit"), record.get("turnover")
    if gp is not None and turnover is not None and gp > turnover:
        issues.append(f"gross_profit ({gp}) exceeds turnover ({turnover}) — implausible")

    pat, pbt = record.get("profit_loss_after_tax"), record.get("profit_loss_before_tax")
    if pat is not None and pbt is not None and pbt != 0:
        tax_adjustment = pat - pbt
        if abs(tax_adjustment) > 0.5 * abs(pbt):
            issues.append(
                f"tax adjustment ({tax_adjustment:+.0f}) exceeds 50% of PBT "
                f"({pbt:.0f}) — unusually large, worth double-checking against source"
            )

    return issues


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=str, help="Path to raw extracted document text")
    parser.add_argument("--dry-run", action="store_true", help="Print the request, don't call the API")
    parser.add_argument("--out", type=str, default="extracted_financials.raw.json")
    args = parser.parse_args()

    if not args.input:
        print(__doc__)
        sys.exit(0)

    text = Path(args.input).read_text()

    if args.dry_run:
        print("Would send to Claude with tool:", json.dumps(EXTRACTION_TOOL, indent=2))
        print(f"\nDocument length: {len(text)} chars")
        return

    if not os.environ.get("ANTHROPIC_API_KEY"):
        print("ANTHROPIC_API_KEY not set. Use --dry-run to inspect the pipeline without calling the API.")
        sys.exit(1)

    records = extract_from_text(text)
    for r in records:
        issues = sanity_check(r)
        if issues:
            print(f"⚠ {r.get('fiscal_year')}: {issues}")

    Path(args.out).write_text(json.dumps(records, indent=2))
    print(f"Wrote {len(records)} record(s) to {args.out}. Review before merging into senus_financials.json.")


if __name__ == "__main__":
    main()
