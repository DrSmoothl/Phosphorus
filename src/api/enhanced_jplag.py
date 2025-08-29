"""Enhanced JPlag API routes with comprehensive comparison and analysis features."""

import os
import tempfile
import zipfile
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..api.jplag_models import (
    ComparisonResult,
    DetailedComparisonRequest,
    ProblemPlagiarismData,
)
from ..api.models import SuccessResponse
from ..common import get_logger, settings
from ..services.enhanced_jplag_service import EnhancedJPlagService

logger = get_logger()

# Create router for enhanced JPlag features
enhanced_jplag_router = APIRouter(prefix="/api/v1/jplag/enhanced", tags=["Enhanced JPlag"])

# Constants for similarity thresholds
HIGH_SIMILARITY_THRESHOLD = 0.8
MEDIUM_SIMILARITY_THRESHOLD = 0.5


def _create_zip_from_directory(directory_path: str) -> str:
    """Create a temporary zip file from a directory."""
    temp_zip = tempfile.NamedTemporaryFile(suffix=".jplag", delete=False)
    temp_zip.close()
    
    with zipfile.ZipFile(temp_zip.name, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for root, _dirs, files in os.walk(directory_path):
            for file in files:
                file_path = os.path.join(root, file)
                arcname = os.path.relpath(file_path, directory_path)
                zipf.write(file_path, arcname)
    
    return temp_zip.name


def get_enhanced_jplag_service() -> EnhancedJPlagService:
    """Get Enhanced JPlag service instance."""
    return EnhancedJPlagService(settings.jplag_jar_path)


@enhanced_jplag_router.get(
    "/problem/{contest_id}/{problem_id}",
    response_model=SuccessResponse[ProblemPlagiarismData],
    summary="Get comprehensive plagiarism data for a problem",
    description="Retrieve detailed plagiarism analysis data for a specific problem in a contest",
)
async def get_problem_plagiarism_data(
    contest_id: str,
    problem_id: int,
    jplag_result_path: Annotated[str | None, Query(description="Path to JPlag result file")] = None,
    enhanced_jplag_service: EnhancedJPlagService = Depends(get_enhanced_jplag_service),
) -> SuccessResponse[ProblemPlagiarismData]:
    """Get comprehensive plagiarism data for a problem."""
    logger.info(f"Getting plagiarism data for contest {contest_id}, problem {problem_id}")

    try:
        # For demo purposes, use the dev jplag file if no path provided
        if not jplag_result_path:
            jplag_result_path = "e:/CAUCOJ/Phosphorus/dev/jplagfile"
            # Convert directory to zip file path if needed
            if os.path.isdir(jplag_result_path):
                jplag_result_path = _create_zip_from_directory(jplag_result_path)

        if not jplag_result_path or not os.path.exists(jplag_result_path):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"JPlag result file not found for contest {contest_id}, problem {problem_id}",
            )

        # Parse comprehensive plagiarism data
        problem_data = await enhanced_jplag_service.parse_problem_plagiarism_data(
            jplag_result_path, problem_id, contest_id
        )

        return SuccessResponse(
            success=True,
            message="Problem plagiarism data retrieved successfully",
            data=problem_data,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get problem plagiarism data: {e!s}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve plagiarism data: {e!s}",
        ) from e


@enhanced_jplag_router.post(
    "/comparison/detailed/enhanced",
    response_model=SuccessResponse[ComparisonResult],
    summary="Get enhanced detailed comparison between two submissions",
    description="Retrieve comprehensive comparison data with code highlighting and match analysis",
)
async def get_enhanced_detailed_comparison(
    request: DetailedComparisonRequest,
    jplag_result_path: Annotated[str | None, Query(description="Path to JPlag result file")] = None,
    enhanced_jplag_service: EnhancedJPlagService = Depends(get_enhanced_jplag_service),
) -> SuccessResponse[ComparisonResult]:
    """Get enhanced detailed comparison between two submissions."""
    logger.info(
        f"Getting enhanced comparison for {request.first_submission} vs {request.second_submission}"
    )

    try:
        # For demo purposes, use the dev jplag file if no path provided
        if not jplag_result_path:
            jplag_result_path = "e:/CAUCOJ/Phosphorus/dev/jplagfile"
            # Convert directory to zip file path if needed
            if os.path.isdir(jplag_result_path):
                jplag_result_path = _create_zip_from_directory(jplag_result_path)

        result = await enhanced_jplag_service.get_detailed_comparison_enhanced(
            request.analysis_id,
            request.first_submission,
            request.second_submission,
            jplag_result_path
        )

        if result is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Enhanced comparison not found",
            )

        return SuccessResponse(
            success=True,
            message="Enhanced detailed comparison retrieved successfully",
            data=result,
        )

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to get enhanced detailed comparison: {e!s}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get enhanced comparison: {e!s}",
        ) from e


@enhanced_jplag_router.get(
    "/analysis/statistics/{contest_id}",
    response_model=SuccessResponse[dict],
    summary="Get comprehensive analysis statistics for a contest",
    description="Retrieve detailed statistics and metrics for plagiarism analysis in a contest",
)
async def get_analysis_statistics(
    contest_id: str,
    problem_ids: Annotated[list[int] | None, Query(description="Specific problem IDs to analyze")] = None,
    enhanced_jplag_service: EnhancedJPlagService = Depends(get_enhanced_jplag_service),
) -> SuccessResponse[dict]:
    """Get comprehensive analysis statistics for a contest."""
    logger.info(f"Getting analysis statistics for contest {contest_id}")

    try:
        # This would typically aggregate data from multiple problem analyses
        # For now, return a sample structure
        statistics = {
            "contest_id": contest_id,
            "total_problems_analyzed": len(problem_ids) if problem_ids else 0,
            "total_submissions": 0,
            "total_comparisons": 0,
            "high_similarity_pairs": 0,
            "clusters_detected": 0,
            "language_distribution": {},
            "similarity_distribution": {
                "very_high": 0,  # > 0.9
                "high": 0,       # 0.7 - 0.9
                "medium": 0,     # 0.5 - 0.7
                "low": 0,        # 0.3 - 0.5
                "very_low": 0    # < 0.3
            },
            "processing_metrics": {
                "total_processing_time_ms": 0,
                "average_processing_time_per_problem_ms": 0,
                "memory_usage_mb": 0
            },
            "problem_breakdown": []
        }

        # If specific problems are requested, analyze them
        if problem_ids:
            for problem_id in problem_ids:
                try:
                    # Get problem data (this would use stored results in production)
                    jplag_result_path = "e:/CAUCOJ/Phosphorus/dev/jplagfile"
                    if os.path.isdir(jplag_result_path):
                        jplag_result_path = _create_zip_from_directory(jplag_result_path)

                    problem_data = await enhanced_jplag_service.parse_problem_plagiarism_data(
                        jplag_result_path, problem_id, contest_id
                    )
                    # Aggregate statistics
                    statistics["total_submissions"] += problem_data.total_submissions
                    statistics["high_similarity_pairs"] += problem_data.high_similarity_count
                    statistics["clusters_detected"] += len(problem_data.clusters)
                    # Add to problem breakdown
                    statistics["problem_breakdown"].append({
                        "problem_id": problem_id,
                        "submissions": problem_data.total_submissions,
                        "high_similarity_pairs": problem_data.high_similarity_count,
                        "max_similarity": problem_data.max_similarity,
                        "clusters": len(problem_data.clusters)
                    })
                    
                except Exception as e:
                    logger.warning(f"Failed to analyze problem {problem_id}: {e}")

        return SuccessResponse(
            success=True,
            message="Analysis statistics retrieved successfully",
            data=statistics,
        )

    except Exception as e:
        logger.error(f"Failed to get analysis statistics: {e!s}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve analysis statistics: {e!s}",
        ) from e


@enhanced_jplag_router.get(
    "/clusters/{contest_id}/{problem_id}",
    response_model=SuccessResponse[list],
    summary="Get detailed cluster analysis for a problem",
    description="Retrieve comprehensive cluster analysis with member details and similarity matrices",
)
async def get_cluster_analysis(
    contest_id: str,
    problem_id: int,
    enhanced_jplag_service: EnhancedJPlagService = Depends(get_enhanced_jplag_service),
) -> SuccessResponse[list]:
    """Get detailed cluster analysis for a problem."""
    logger.info(f"Getting cluster analysis for contest {contest_id}, problem {problem_id}")

    try:
        # Get problem data
        jplag_result_path = "e:/CAUCOJ/Phosphorus/dev/jplagfile"
        
        if os.path.isdir(jplag_result_path):
            jplag_result_path = _create_zip_from_directory(jplag_result_path)

        problem_data = await enhanced_jplag_service.parse_problem_plagiarism_data(
            jplag_result_path, problem_id, contest_id
        )

        # Enhance cluster data with additional analysis
        enhanced_clusters = []
        for cluster in problem_data.clusters:
            enhanced_cluster = {
                "index": cluster.index,
                "size": cluster.size,
                "average_similarity": cluster.average_similarity,
                "strength": cluster.strength,
                "members": cluster.members,
                "dominant_language": cluster.dominant_language,
                "similarity_matrix": cluster.similarity_matrix,
                "risk_level": "high" if cluster.average_similarity > HIGH_SIMILARITY_THRESHOLD else "medium" if cluster.average_similarity > MEDIUM_SIMILARITY_THRESHOLD else "low",
                "recommended_action": "immediate_review" if cluster.average_similarity > HIGH_SIMILARITY_THRESHOLD else "manual_check" if cluster.average_similarity > MEDIUM_SIMILARITY_THRESHOLD else "monitor"
            }
            enhanced_clusters.append(enhanced_cluster)

        return SuccessResponse(
            success=True,
            message="Cluster analysis retrieved successfully",
            data=enhanced_clusters,
        )

    except Exception as e:
        logger.error(f"Failed to get cluster analysis: {e!s}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve cluster analysis: {e!s}",
        ) from e
