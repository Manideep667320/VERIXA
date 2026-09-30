"""API router aggregation — single import for main.py."""

from fastapi import APIRouter

from app.api.agent import router as agent_router
from app.api.approval import router as approval_router
from app.api.audit import router as audit_router

api_router = APIRouter(prefix="/api")
api_router.include_router(agent_router)
api_router.include_router(approval_router)
api_router.include_router(audit_router)
