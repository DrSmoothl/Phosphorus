"""Hydro OJ integration API routes."""

from fastapi import APIRouter, Depends, HTTPException, status

from ..api.hydro_models import (
    ContestPlagiarismRequest,
    ContestProblemSelectionRequest,
    PlagiarismResult,
    ContestInfo,
    ProblemInfo,
    LanguageStats
)
from ..api.models import SuccessResponse
from ..common import get_database, get_logger, settings
from ..services import JPlagService
from ..services.hydro_service import HydroService

logger = get_logger()

# Create router
hydro_router = APIRouter(prefix="/api/v1", tags=["Hydro"])


async def get_hydro_service() -> HydroService:
    """Get Hydro service instance."""
    database = await get_database()
    jplag_service = JPlagService(settings.jplag_jar_path)
    return HydroService(database, jplag_service)


@hydro_router.post(
    "/contest/plagiarism",
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


@hydro_router.post(
    "/contest/plagiarism/problems",
    response_model=SuccessResponse[list[PlagiarismResult]],
    summary="Check plagiarism for selected contest problems",
    description="Analyze selected problems in a contest for plagiarism using JPlag",
)
async def check_contest_problems_plagiarism(
    request: ContestProblemSelectionRequest,
    hydro_service: HydroService = Depends(get_hydro_service),
) -> SuccessResponse[list[PlagiarismResult]]:
    """Check plagiarism for selected contest problems."""
    logger.info(f"Starting plagiarism check for contest {request.contest_id} with problems {request.problem_ids}")

    try:
        results = await hydro_service.check_contest_problems_plagiarism(request)

        return SuccessResponse(
            success=True,
            message=f"Contest plagiarism check completed for {len(results)} problems",
            data=results,
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
    "/contest/{contest_id}/plagiarism",
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


@hydro_router.get(
    "/contests/plagiarism",
    response_model=SuccessResponse[list[ContestInfo]],
    summary="Get all contests with plagiarism results",
    description="Retrieve all contests that have plagiarism check results",
)
async def get_contests_with_plagiarism(
    hydro_service: HydroService = Depends(get_hydro_service),
) -> SuccessResponse[list[ContestInfo]]:
    """Get all contests with plagiarism results."""
    logger.info("Getting all contests with plagiarism results")

    try:
        contests = await hydro_service.get_contests_with_plagiarism()

        return SuccessResponse(
            success=True,
            message=f"Found {len(contests)} contests with plagiarism results",
            data=contests,
        )

    except Exception as e:
        logger.error(f"Failed to get contests with plagiarism: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get contests: {e}",
        ) from e


@hydro_router.get(
    "/contest/{contest_id}/problems",
    response_model=SuccessResponse[list[ProblemInfo]],
    summary="Get contest problems",
    description="Retrieve all problems in a contest with submission statistics",
)
async def get_contest_problems(
    contest_id: str,
    hydro_service: HydroService = Depends(get_hydro_service),
) -> SuccessResponse[list[ProblemInfo]]:
    """Get contest problems."""
    logger.info(f"Getting problems for contest {contest_id}")

    try:
        problems = await hydro_service.get_contest_problems(contest_id)

        return SuccessResponse(
            success=True,
            message=f"Found {len(problems)} problems in contest",
            data=problems,
        )

    except Exception as e:
        logger.error(f"Failed to get contest problems: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get problems: {e}",
        ) from e


@hydro_router.get(
    "/contest/{contest_id}/problem/{problem_id}/languages",
    response_model=SuccessResponse[list[LanguageStats]],
    summary="Get problem language statistics",
    description="Retrieve language usage statistics for a specific problem",
)
async def get_problem_language_stats(
    contest_id: str,
    problem_id: int,
    hydro_service: HydroService = Depends(get_hydro_service),
) -> SuccessResponse[list[LanguageStats]]:
    """Get problem language statistics."""
    logger.info(f"Getting language stats for problem {problem_id} in contest {contest_id}")

    try:
        stats = await hydro_service.get_problem_language_stats(contest_id, problem_id)

        return SuccessResponse(
            success=True,
            message=f"Found statistics for {len(stats)} languages",
            data=stats,
        )

    except Exception as e:
        logger.error(f"Failed to get language stats: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get language stats: {e}",
        ) from e


@hydro_router.get(
    "/contest/{contest_id}/problem/{problem_id}/plagiarism",
    response_model=SuccessResponse[PlagiarismResult | None],
    summary="Get problem plagiarism result",
    description="Retrieve plagiarism check result for a specific problem",
)
async def get_problem_plagiarism_result(
    contest_id: str,
    problem_id: int,
    hydro_service: HydroService = Depends(get_hydro_service),
) -> SuccessResponse[PlagiarismResult | None]:
    """Get problem plagiarism result."""
    logger.info(f"Getting plagiarism result for problem {problem_id} in contest {contest_id}")

    try:
        result = await hydro_service.get_problem_plagiarism_result(contest_id, problem_id)

        return SuccessResponse(
            success=True,
            message="Found plagiarism result" if result else "No plagiarism result found",
            data=result,
        )

    except Exception as e:
        logger.error(f"Failed to get problem plagiarism result: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get plagiarism result: {e}",
        ) from e
