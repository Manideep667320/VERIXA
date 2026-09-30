"""Evidence-to-Action Enterprise AI Agent — FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import settings
from app.core.database import init_db
from app.models import HealthResponse

# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.log_level),
    format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Startup/shutdown lifecycle — initialize DB, load tools."""
    logger.info("Starting Evidence-to-Action Agent...")
    init_db()
    logger.info("Database initialized.")

    # Import tools package to trigger @register_tool decorators
    import app.tools  # noqa: F401
    from app.tools.registry import list_tools
    logger.info("Registered tools: %s", list_tools())

    yield
    logger.info("Shutting down.")


app = FastAPI(
    title="Evidence-to-Action Enterprise AI Agent",
    description="Policy-aware, risk-controlled, evidence-backed workflow automation.",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — allow frontend dev server
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_url, "http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount all API routes
app.include_router(api_router)


@app.get("/api/health", response_model=HealthResponse, tags=["health"])
async def health_check():
    """Health check endpoint."""
    return HealthResponse()
