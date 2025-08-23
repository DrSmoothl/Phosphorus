"""Hydro OJ integration API routes."""

from fastapi import APIRouter, Depends, HTTPException, status

from ..api.hydro_models import ContestPlagiarismRequest, PlagiarismResult
from ..api.models import SuccessResponse
from ..common import get_database, get_logger, settings
from ..services import JPlagService
from ..services.hydro_service import HydroService

logger = get_logger()

# Create router
hydro_router = APIRouter(prefix="/api/v1/contest", tags=["Hydro"])


async def get_hydro_service() -> HydroService:
    """Get Hydro service instance."""
    database = await get_database()
    jplag_service = JPlagService(settings.jplag_jar_path)
    return HydroService(database, jplag_service)


@hydro_router.post(
    "/plagiarism",
    response_model=SuccessResponse[PlagiarismResult],
    summary="Check plagiarism for contest submissions",
    description="Analyze all accepted submissions in a contest for plagiarism using JPlag",
)
async def check_contest_plagiarism(
    request: ContestPlagiarismRequest,
    hydro_service: HydroService = Depends(get_hydro_service),
) -> SuccessResponse[PlagiarismResult]:
    """Check plagiarism for contest submissions."""
    logger.info(f"Starting plagiarism check for contest {request.contest_id}")

    try:
        result = await hydro_service.check_contest_plagiarism(request)

        return SuccessResponse(
            success=True,
            message="Contest plagiarism check completed successfully",
            data=result,
        )

    except ValueError as e:
        logger.warning(f"Invalid request for contest {request.contest_id}: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        ) from e

    except Exception as e:
        logger.error(f"Contest plagiarism check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Plagiarism check failed: {e}",
        ) from e


@hydro_router.get(
    "/{contest_id}/plagiarism",
    response_model=SuccessResponse[list[PlagiarismResult]],
    summary="Get plagiarism results for contest",
    description="Retrieve all plagiarism check results for a contest",
)
async def get_contest_plagiarism_results(
    contest_id: str,
    hydro_service: HydroService = Depends(get_hydro_service),
) -> SuccessResponse[list[PlagiarismResult]]:
    """Get plagiarism results for a contest."""
    logger.info(f"Getting plagiarism results for contest {contest_id}")

    try:
        results = await hydro_service.get_contest_plagiarism_results(contest_id)

        return SuccessResponse(
            success=True,
            message=f"Found {len(results)} plagiarism results",
            data=results,
        )

    except Exception as e:
        logger.error(f"Failed to get plagiarism results: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get results: {e}",
        ) from e
