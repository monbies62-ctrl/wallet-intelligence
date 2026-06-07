"""Wallet Intelligence application."""

from __future__ import annotations

import asyncio
import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from wallet_intelligence.core.config import settings
from wallet_intelligence.core.database import init_db, close_db
from wallet_intelligence.core.redis import close_redis
from wallet_intelligence.api.routes.wallets import router as wallets_router
from wallet_intelligence.api.routes.analytics import router as analytics_router
from wallet_intelligence.api.routes.alerts import router as alerts_router
from wallet_intelligence.api.websocket.live import router as ws_router

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle."""
    logger.info("Starting Wallet Intelligence...")
    await init_db()
    yield
    logger.info("Shutting down...")
    await close_db()
    await close_redis()


def create_app() -> FastAPI:
    """Create FastAPI application."""
    app = FastAPI(
        title="Wallet Intelligence",
        description="Real-time wallet tracking, whale monitoring, and smart money analytics",
        version="0.1.0",
        lifespan=lifespan,
    )

    # CORS
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Routes
    app.include_router(wallets_router)
    app.include_router(analytics_router)
    app.include_router(alerts_router)
    app.include_router(ws_router)

    # Health check
    @app.get("/health")
    async def health():
        return {"status": "ok", "version": "0.1.0"}

    return app


app = create_app()
