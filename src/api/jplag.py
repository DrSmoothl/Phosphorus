"""JPlag API routes."""

from typing import Annotated

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from ..api.jplag_models import (
    DetailedComparisonRequest,
    PlagiarismAnalysisRequest,
    PlagiarismAnalysisResult,
    ProgrammingLanguage,
)
from ..api.models import SuccessResponse
from ..common import get_logger, settings
from ..services import JPlagService

logger = get_logger()

# Create router
jplag_router = APIRouter(prefix="/api/v1/jplag", tags=["JPlag"])


def get_jplag_service() -> JPlagService:
    """Get JPlag service instance."""
    return JPlagService(settings.jplag_jar_path)


@jplag_router.post(
    "/analyze",
    response_model=SuccessResponse[PlagiarismAnalysisResult],
    summary="Analyze submissions for plagiarism",
    description="Upload multiple source code files and analyze them for plagiarism using JPlag",
)
async def analyze_plagiarism(
    files: Annotated[
        list[UploadFile], File(description="Source code files to analyze")
    ],
    language: Annotated[
        ProgrammingLanguage, Form(description="Programming language")
    ] = ProgrammingLanguage.JAVA,
    min_tokens: Annotated[
        int, Form(ge=1, le=100, description="Minimum token match threshold")
    ] = 9,
    similarity_threshold: Annotated[
        float, Form(ge=0.0, le=1.0, description="Similarity threshold")
    ] = 0.0,
    base_code_included: Annotated[
        bool, Form(description="Whether base code is included")
    ] = False,
    normalize_tokens: Annotated[
        bool, Form(description="Whether to normalize tokens")
    ] = False,
    jplag_service: JPlagService = Depends(get_jplag_service),
) -> SuccessResponse[PlagiarismAnalysisResult]:
    """Analyze submissions for plagiarism."""
    if not files:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No files provided for analysis",
        )

    if len(files) < 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="At least 2 files are required for comparison",
        )

    logger.info(f"Starting plagiarism analysis for {len(files)} files")

    try:
        # Create request object
        request = PlagiarismAnalysisRequest(
            language=language,
            min_tokens=min_tokens,
            similarity_threshold=similarity_threshold,
            base_code_included=base_code_included,
            normalize_tokens=normalize_tokens,
        )

        # Run analysis
        result = await jplag_service.analyze_submissions(files, request)

        return SuccessResponse(
            success=True,
            message="Plagiarism analysis completed successfully",
            data=result,
        )

    except Exception as e:
        logger.error(f"Plagiarism analysis failed: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Analysis failed: {str(e)}",
        ) from e


@jplag_router.post(
    "/comparison/detailed",
    response_model=SuccessResponse[dict],
    summary="Get detailed comparison between two submissions",
    description="Retrieve detailed comparison data between two specific submissions",
)
async def get_detailed_comparison(
    request: DetailedComparisonRequest,
    jplag_service: JPlagService = Depends(get_jplag_service),
) -> SuccessResponse[dict]:
    """Get detailed comparison between two submissions."""
    logger.info(
        f"Getting detailed comparison for {request.first_submission} vs {request.second_submission}"
    )

    try:
        result = await jplag_service.get_detailed_comparison(
            request.analysis_id, request.first_submission, request.second_submission
        )

        if result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Comparison not found",
            )

        return SuccessResponse(
            success=True,
            message="Detailed comparison retrieved successfully",
            data=result.model_dump(),
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get detailed comparison: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get comparison: {str(e)}",
        ) from e


@jplag_router.get(
    "/languages",
    response_model=SuccessResponse[list[str]],
    summary="Get supported programming languages",
    description="Retrieve list of programming languages supported by JPlag",
)
async def get_supported_languages() -> SuccessResponse[list[str]]:
    """Get list of supported programming languages."""
    languages = [lang.value for lang in ProgrammingLanguage]
    return SuccessResponse(
        success=True,
        message="Supported languages retrieved successfully",
        data=languages,
    )
