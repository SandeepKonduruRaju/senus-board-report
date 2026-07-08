"""
'Ask the Board Pack' — natural-language Q&A grounded in live database queries.

Architecture: this is a genuine tool-calling agent loop, not a single call
with the whole dataset stuffed into the prompt. Claude is given a small set
of named tools (see chat_tools.py) and decides for itself which ones it
needs to answer a given question; the backend executes exactly those
queries against the real database and feeds the results back. The API
response includes which tools were called and with what arguments, so any
answer is fully auditable — you can see exactly what data grounded it.

Why this matters for a board report tool specifically: a Board member asking
"how has our customer concentration changed" shouldn't get an answer
hallucinated from the model's training data about SaaS companies in general —
it should get an answer derived from tool calls that actually queried Senus's
own FY2024/FY2025/H1 FY2026 figures, and be able to see that happened.

Requires ANTHROPIC_API_KEY — unlike the insights endpoint, there isn't a
meaningful deterministic fallback for open-ended natural-language Q&A. A
lightweight pattern-matched fallback handles a few common questions so the
feature is still demoable without a key; anything else returns a clear
"configure ANTHROPIC_API_KEY" message rather than a wrong answer.
"""
import logging
import os
from typing import Any

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from .. import models
from ..chat_tools import TOOL_SCHEMAS, call_tool
from ..database import get_db

log = logging.getLogger(__name__)

router = APIRouter(prefix="/api/chat", tags=["chat"])

MODEL = "claude-sonnet-4-6"
MAX_TOOL_ITERATIONS = 5  # hard cap so a confused loop can't run away

SYSTEM_PROMPT = """You are answering questions about Senus PLC's board pack \
for whoever is asking — could be the CEO, a Board member, an equity investor, \
or a credit provider. You have tools to query the actual database; use them \
rather than answering from general knowledge or assumption. Rules:

1. Call tools to get real data before answering. Never state a specific \
   figure you haven't retrieved via a tool call in this conversation.
2. If asked about EBITDA, ROCE, DSCR, or Current Ratio, call \
   get_disclosure_gaps and use its explanation — do not derive your own \
   version of these metrics from raw figures.
3. If the data needed to answer isn't available from any tool, say so \
   plainly rather than guessing.
4. Be direct and specific. Cite the actual numbers you retrieved. Keep \
   answers under 150 words unless the question genuinely requires more.
5. If a question compares periods, call get_annual_financials for each \
   period you need rather than assuming you already know the figures.
"""


class ChatMessage(BaseModel):
    role: str  # "user" | "assistant"
    content: str


class ChatRequest(BaseModel):
    message: str
    history: list[ChatMessage] = []


class ToolCallRecord(BaseModel):
    tool: str
    input: dict[str, Any]


class ChatResponse(BaseModel):
    answer: str
    tool_calls: list[ToolCallRecord]
    generated_by: str


# ---------------------------------------------------------------------------
# Lightweight fallback for demo use without an API key
# ---------------------------------------------------------------------------

def _keyword_fallback(question: str, db: Session) -> str | None:
    """Handles a handful of common questions without an LLM, so the feature
    is still demoable with no API key configured. Returns None if the
    question doesn't match anything — caller shows a 'configure API key'
    message in that case rather than a wrong guess."""
    q = question.lower()

    f25 = db.query(models.AnnualFinancial).filter_by(fiscal_year="FY2025").first()
    h1 = db.query(models.AnnualFinancial).filter_by(fiscal_year="H1_FY2026").first()

    if "revenue" in q and f25:
        return (
            f"FY2025 revenue was €{f25.turnover:,.0f}. "
            f"H1 FY2026 revenue was €{h1.turnover:,.0f}, up 4.1% on H1 FY2025 "
            f"(unaudited). [Answered via keyword match — configure "
            f"ANTHROPIC_API_KEY for full natural-language Q&A.]"
        )
    if "ebitda" in q:
        gaps = call_tool(db, "get_disclosure_gaps", {})
        ebitda_note = next(g for g in gaps["gaps"] if g["metric"] == "EBITDA")
        return (
            f"{ebitda_note['why_not_shown']} "
            f"[Answered via keyword match — configure ANTHROPIC_API_KEY for "
            f"full natural-language Q&A.]"
        )
    if "cash" in q and f25:
        return (
            f"Cash at 30 June 2025 was €{f25.cash_end:,.0f}. "
            f"By 31 Dec 2025 (H1 FY2026, unaudited) it had grown to "
            f"€{h1.cash_end:,.0f} following the €1.1m December 2025 placement. "
            f"[Answered via keyword match — configure ANTHROPIC_API_KEY for "
            f"full natural-language Q&A.]"
        )
    return None


# ---------------------------------------------------------------------------
# Endpoint
# ---------------------------------------------------------------------------

@router.post("", response_model=ChatResponse, summary="Ask the board pack a question")
def chat(req: ChatRequest, db: Session = Depends(get_db)) -> ChatResponse:
    api_key = os.environ.get("ANTHROPIC_API_KEY")

    if not api_key:
        fallback = _keyword_fallback(req.message, db)
        if fallback:
            return ChatResponse(answer=fallback, tool_calls=[], generated_by="keyword-fallback")
        raise HTTPException(
            status_code=503,
            detail=(
                "This question needs live AI Q&A. Set ANTHROPIC_API_KEY to enable it, "
                "or try asking about revenue, cash, or EBITDA for a fallback answer."
            ),
        )

    import anthropic

    client = anthropic.Anthropic(api_key=api_key)

    messages: list[dict[str, Any]] = [
        {"role": m.role, "content": m.content} for m in req.history
    ]
    messages.append({"role": "user", "content": req.message})

    tool_calls_made: list[ToolCallRecord] = []

    for _ in range(MAX_TOOL_ITERATIONS):
        response = client.messages.create(
            model=MODEL,
            max_tokens=700,
            system=SYSTEM_PROMPT,
            tools=TOOL_SCHEMAS,
            messages=messages,
        )

        if response.stop_reason != "tool_use":
            final_text = "".join(
                b.text for b in response.content if b.type == "text"
            )
            return ChatResponse(
                answer=final_text,
                tool_calls=tool_calls_made,
                generated_by=MODEL,
            )

        # Model wants to call one or more tools — execute them and continue the loop
        messages.append({"role": "assistant", "content": response.content})

        tool_results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            result = call_tool(db, block.name, block.input)
            tool_calls_made.append(ToolCallRecord(tool=block.name, input=block.input))
            tool_results.append({
                "type": "tool_result",
                "tool_use_id": block.id,
                "content": str(result),
            })

        messages.append({"role": "user", "content": tool_results})

    log.warning("Chat tool loop hit MAX_TOOL_ITERATIONS without a final answer.")
    return ChatResponse(
        answer=(
            "I gathered some data but couldn't settle on a final answer within "
            "the allowed number of steps — try rephrasing or asking a more "
            "specific question."
        ),
        tool_calls=tool_calls_made,
        generated_by=MODEL,
    )
