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

    # Ensure ChromaDB knowledge base collection exists and is seeded
    try:
        import chromadb
        from app.knowledge.retrieval import _default_persist_dir, _COLLECTION_NAME
        from app.knowledge.ingestion import ingest_all

        persist_dir = _default_persist_dir()
        client = chromadb.PersistentClient(path=str(persist_dir))
        existing_collections = [c.name for c in client.list_collections()]
        if _COLLECTION_NAME not in existing_collections or client.get_collection(_COLLECTION_NAME).count() == 0:
            logger.info("ChromaDB collection '%s' missing or empty. Auto-ingesting knowledge base...", _COLLECTION_NAME)
            ingest_res = ingest_all(persist_dir=persist_dir)
            logger.info("ChromaDB auto-ingestion complete: %s", ingest_res)
        else:
            logger.info(
                "ChromaDB collection '%s' ready (%d chunks).",
                _COLLECTION_NAME,
                client.get_collection(_COLLECTION_NAME).count(),
            )
    except Exception as exc:
        logger.warning("ChromaDB startup check notice: %s", exc)

    yield
    logger.info("Shutting down.")


app = FastAPI(
    title="Evidence-to-Action Enterprise AI Agent",
    description="Policy-aware, risk-controlled, evidence-backed workflow automation.",
    version="0.1.0",
    lifespan=lifespan,
)

# CORS — allow frontend dev server and production deployments (e.g. Vercel)
allowed_origins = [
    origin.strip() for origin in settings.frontend_url.split(",") if origin.strip()
] + ["http://localhost:5173", "http://localhost:3000"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_origin_regex=r"https://.*\.vercel\.app",
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
