"""
Senus PLC Board Report — FastAPI application entrypoint.
"""
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import financials, insights, chat

app = FastAPI(
    title="Senus PLC Board Report API",
    description=(
        "Serves audited financial data, derived KPIs, and AI-generated "
        "board commentary for the Senus PLC Board Report platform."
    ),
    version="1.0.0",
)

_raw_origins = os.environ.get("ALLOWED_ORIGINS", "*")
_origins = [o.strip() for o in _raw_origins.split(",")] if _raw_origins != "*" else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["GET", "POST"],
    allow_headers=["*"],
)

app.include_router(financials.router)
app.include_router(insights.router)
app.include_router(chat.router)


@app.get("/", tags=["meta"])
def root() -> dict:
    return {"status": "ok", "service": "senus-board-report-api", "version": "1.0.0"}


@app.get("/health", tags=["meta"])
def health() -> dict:
    return {"status": "healthy"}
