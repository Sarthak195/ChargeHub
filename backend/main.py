import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os

from database import init_db
from scheduler import start_scheduler, stop_scheduler
from routers import auth, plugs, sessions, analytics, payments, coins
from config import get_settings

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)
settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("ChargeHub starting up...")
    await init_db()
    start_scheduler()
    yield
    stop_scheduler()
    logger.info("ChargeHub shut down.")


app = FastAPI(
    title="ChargeHub API",
    description="Local EV Smart Plug Management Platform for Apartment Complexes",
    version="1.0.0",
    lifespan=lifespan,
)

# CORS — allow the React dev server in development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000", "http://localhost:8000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API Routers
app.include_router(auth.router)
app.include_router(plugs.router)
app.include_router(sessions.router)
app.include_router(analytics.router)
app.include_router(payments.router)
app.include_router(coins.router)


@app.get("/api/health")
async def health():
    return {"status": "ok", "version": "1.0.0"}


# Serve React SPA in production (when frontend is built into backend/static/)
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")
