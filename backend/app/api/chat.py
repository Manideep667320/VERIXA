"""Read-only, tenant-scoped chatbot endpoint."""

from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Header, HTTPException
from pydantic import BaseModel, ConfigDict, Field

from app.chat.agent import ChatResponse, run_chat_turn

router = APIRouter(prefix="/chat", tags=["chat"])


class ChatTurnRequest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    message: str = Field(min_length=1, max_length=10_000)
    thread_id: str | None = Field(default=None, min_length=1, max_length=100)


@router.post("/turn", response_model=ChatResponse)
async def chat_turn(
    body: ChatTurnRequest,
    tenant_id: Annotated[str, Header(alias="X-Tenant-ID", min_length=1, max_length=100)],
) -> ChatResponse:
    try:
        return await run_chat_turn(body.message, tenant_id=tenant_id, thread_id=body.thread_id)
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
