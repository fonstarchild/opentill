"""
Opentill backend — lightweight FastAPI server.

Runs as a sidecar process launched by Tauri. Listens on 127.0.0.1 only
(never exposed to the network). Port is configurable via OPENTILL_PORT env
variable (default 47821).

Database: SQLite (opentill.db) by default.
For multi-terminal setups, set DATABASE_URL to a PostgreSQL connection string.
"""
import logging
import os
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from sqlmodel import SQLModel

from .database import engine
from .shared.domain.exceptions import DomainException

# ── Import SQLModel table models so they're registered before create_all ──────
from .catalog.infrastructure.sqlmodel_models import ProductTable  # noqa: F401
from .sales.infrastructure.sqlmodel_models import OrderTable, OrderItemTable  # noqa: F401

# ── DDD routers ───────────────────────────────────────────────────────────────
from .catalog.interfaces.router import router as catalog_router
from .sales.interfaces.router import router as sales_router
from .payments.interfaces.router import router as payments_router
from .ecommerce.interfaces.router import router as ecommerce_router
from .configuration.interfaces.router import router as config_router

logger = logging.getLogger("opentill")
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")


@asynccontextmanager
async def lifespan(app: FastAPI):
    SQLModel.metadata.create_all(engine)
    logger.info("Database tables created/verified")
    yield


app = FastAPI(
    title="Opentill API",
    version="0.1.0",
    docs_url="/docs",
    lifespan=lifespan,
)

# ── CORS ──────────────────────────────────────────────────────────────────────
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://tauri.localhost",
        "tauri://localhost",
    ],
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request logging middleware ────────────────────────────────────────────────
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start = time.time()
    response = await call_next(request)
    duration_ms = (time.time() - start) * 1000
    logger.info(
        "%s %s → %d (%.1fms)",
        request.method,
        request.url.path,
        response.status_code,
        duration_ms,
    )
    return response


# ── Global domain exception handler ──────────────────────────────────────────
@app.exception_handler(DomainException)
async def domain_exception_handler(request: Request, exc: DomainException):
    return JSONResponse(
        status_code=exc.http_status,
        content={"detail": exc.message},
    )


# ── Routers ───────────────────────────────────────────────────────────────────
app.include_router(catalog_router,   prefix="/api/catalog",    tags=["catalog"])
app.include_router(sales_router,     prefix="/api/orders",     tags=["orders"])
app.include_router(payments_router,  prefix="/api/payments",   tags=["payments"])
app.include_router(ecommerce_router, prefix="/api/ecommerce",  tags=["ecommerce"])
app.include_router(config_router,    prefix="/api/config",     tags=["config"])


@app.get("/api/health")
def health():
    return {"status": "ok", "version": "0.1.0"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("OPENTILL_PORT", 47821))
    uvicorn.run("backend.main:app", host="127.0.0.1", port=port, reload=False)
