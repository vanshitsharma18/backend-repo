"""Health check route — used by Cloud Run liveness probes."""

from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(
    prefix="/api/health",
    tags=["Health"]
)


class HealthResponse(BaseModel):
    status: str


@router.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description=(
        "Returns the current health status of the API. "
        "Used by Cloud Run readiness and liveness probes."
    ),
)
async def health_check() -> HealthResponse:
    return HealthResponse(status="healthy")
