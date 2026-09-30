"""Agent API routes — POST /agent/run, GET /agent/{run_id}."""

from fastapi import APIRouter

from app.models import AgentRunRequest, AgentRunResponse, HealthResponse

router = APIRouter(prefix="/agent", tags=["agent"])


@router.post("/run", response_model=AgentRunResponse)
async def run_agent(request: AgentRunRequest) -> AgentRunResponse:
    """Accept a natural-language request and run the agent pipeline."""
    # TODO: Wire to agent graph
    return AgentRunResponse(
        run_id="RUN-PLACEHOLDER",
        status="NOT_IMPLEMENTED",
        final_response="Agent pipeline not yet implemented.",
    )


@router.get("/{run_id}", response_model=AgentRunResponse)
async def get_run(run_id: str) -> AgentRunResponse:
    """Retrieve the state of a previous agent run."""
    # TODO: Fetch from database
    return AgentRunResponse(
        run_id=run_id,
        status="NOT_FOUND",
        final_response="Run lookup not yet implemented.",
    )
