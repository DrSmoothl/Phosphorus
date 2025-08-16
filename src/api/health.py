"""Health check API routes."""

from datetime import UTC, datetime

from fastapi import APIRouter

from ..api.models import HealthResponse
from ..common import get_logger

router = APIRouter(prefix="/api/v1", tags=["health"])
logger = get_logger()


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    """Health check endpoint."""
    logger.info("Health check requested")

    return HealthResponse(
        success=True,
        message="Service is healthy",
        status="healthy",
        timestamp=datetime.now(UTC).isoformat(),
    )
