"""API router aggregation — single import for main.py."""

from fastapi import APIRouter

from app.api.analytics import router as analytics_router
from app.api.agent import router as agent_router
from app.api.approval import router as approval_router
from app.api.audit import router as audit_router
from app.api.insights import router as insights_router
from app.api.policy import router as policy_router
from app.api.shadow import router as shadow_router

api_router = APIRouter(prefix="/api")
api_router.include_router(agent_router)
api_router.include_router(approval_router)
api_router.include_router(audit_router)
api_router.include_router(insights_router)
api_router.include_router(policy_router)
api_router.include_router(shadow_router)
api_router.include_router(analytics_router)
