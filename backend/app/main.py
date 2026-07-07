"""
Senus PLC Board Report — FastAPI application entrypoint.

Registers routers, configures CORS, and exposes health/root endpoints.
"""
import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .routers import financials, insights

# ---------------------------------------------------------------------------
# Application factory
# ---------------------------------------------------------------------------

app = FastAPI(
    title="Senus PLC Board Report API",
    description=(
        "Serves audited financial data, derived KPIs, and AI-generated "
        "board commentary for the Senus PLC Board Report platform."
    ),
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

# In production, restrict this to the exact frontend origin.
# Reads from ALLOWED_ORIGINS env var (comma-separated); defaults to * for local dev.
_raw_origins = os.environ.get("ALLOWED_ORIGINS", "*")
_origins = [o.strip() for o in _raw_origins.split(",")] if _raw_origins != "*" else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=True,
    allow_methods=["GET"],      # this API is read-only
    allow_headers=["*"],
)

app.include_router(financials.router)
app.include_router(insights.router)


# ---------------------------------------------------------------------------
# Health endpoints
# ---------------------------------------------------------------------------

@app.get("/", tags=["meta"], summary="Root")
def root() -> dict:
    return {"status": "ok", "service": "senus-board-report-api", "version": "1.0.0"}


@app.get("/health", tags=["meta"], summary="Health check")
def health() -> dict:
    """Used by load balancers / deploy platforms to verify the service is alive."""
    return {"status": "healthy"}
