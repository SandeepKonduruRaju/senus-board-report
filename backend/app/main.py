"""
Senus PLC Board Report — FastAPI application entrypoint.
"""
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from . import models
from .database import SessionLocal
from .routers import financials, insights, chat

log = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Auto-seed the database on startup if it's empty.

    This matters specifically for platforms like Render, where the Start
    Command just runs uvicorn directly — there's no separate step that runs
    `python -m data.seed_db` the way there was in local development. Without
    this, a freshly-deployed backend has an empty (but schema-valid) SQLite
    file, and every endpoint 500s trying to read data that was never loaded.

    Tables are created first (idempotent — a no-op if they already exist),
    since on a truly fresh database even the emptiness-check below would
    fail with "no such table" otherwise.

    IMPORTANT: the check session is explicitly closed BEFORE calling seed(),
    not after. seed() does its own DROP TABLE / CREATE TABLE via a separate
    connection from the same engine's pool — if the check session here is
    still open (even just holding an uncommitted read) when that happens,
    SQLite can raise "database is locked" since one connection is dropping
    tables the other still has open. This was a real bug caught only in
    production (Render), not in local testing, because SQLite's locking
    behaviour under concurrent-connection pressure is timing-dependent.
    """
    from .database import Base, engine

    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    is_empty = db.query(models.Company).first() is None
    db.close()  # release before seed() touches the schema, not after

    if is_empty:
        log.info("Database is empty — running initial seed...")
        from data.seed_db import seed
        seed()
    else:
        log.info("Database already seeded, skipping.")

    yield


app = FastAPI(
    title="Senus PLC Board Report API",
    description=(
        "Serves audited financial data, derived KPIs, and AI-generated "
        "board commentary for the Senus PLC Board Report platform."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# CORS: this API never uses cookies or credentialed requests (the login
# gate uses sessionStorage, not cookies), so allow_credentials is
# deliberately False. That makes allow_origins=["*"] work simply and
# reliably — combining allow_credentials=True with a wildcard origin is
# legal but fragile, and was the cause of a real CORS failure in production
# (browsers/some proxies handle that combination inconsistently). If this
# API ever needs cookie-based auth, allow_credentials=True must be paired
# with an explicit origin list (via ALLOWED_ORIGINS), never "*".
_raw_origins = os.environ.get("ALLOWED_ORIGINS", "*")
_origins = [o.strip() for o in _raw_origins.split(",")] if _raw_origins != "*" else ["*"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=_origins,
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
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
