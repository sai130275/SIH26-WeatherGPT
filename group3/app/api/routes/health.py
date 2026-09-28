"""
api/routes/health.py
--------------------
GET /health — liveness probe.

Used by Group 2 (Node.js backend) and any orchestration layer to verify
that the Group 3 service is running and reachable before issuing
weather/AI requests.
"""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(tags=["Health"])


class HealthResponse(BaseModel):
    """Schema for the health-check response body."""

    status: str

    model_config = {"json_schema_extra": {"example": {"status": "ok"}}}


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Service liveness check",
    description=(
        "Returns `{'status': 'ok'}` when the service is running. "
        "Intended for use by load balancers, the Node.js backend (Group 2), "
        "and CI pipelines."
    ),
)
async def health_check() -> HealthResponse:
    """Liveness probe — always returns 200 OK when the process is alive."""
    return HealthResponse(status="ok")
