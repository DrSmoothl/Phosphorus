"""Demo script for Hydro OJ integration."""

import asyncio
import os
import traceback
from datetime import datetime

from bson import ObjectId

from src.api.hydro_models import ContestPlagiarismRequest, SubmissionStatus
from src.common import get_database, settings
from src.services import JPlagService
from src.services.hydro_service import HydroService


async def create_demo_data():
    """Create demo contest and submissions data."""
    db = await get_database()

    # Create a demo contest
    contest_id = ObjectId()
    print(f"Creating demo contest: {contest_id}")

    # Create demo submissions
    submissions = [
        {
            "_id": ObjectId(),
            "status": SubmissionStatus.ACCEPTED,
            "uid": 21,
            "code": """
def hello():
    print("Hello World!")
    return "success"

if __name__ == "__main__":
    hello()
""",
            "lang": "py.py3",
            "pid": 1001,
            "domainId": "system",
            "score": 100,
            "time": 150.0,
            "memory": 408,
            "judgeTexts": [],
            "compilerTexts": [],
            "testCases": [],
            "judger": 1,
            "judgeAt": datetime.utcnow(),
            "rejudged": False,
            "contest": contest_id,
            "files": {},
            "subtasks": {},
        },
        {
            "_id": ObjectId(),
            "status": SubmissionStatus.ACCEPTED,
            "uid": 22,
            "code": """
def hello():
    print("Hello World!")
    return "success"

if __name__ == "__main__":
    hello()
""",
            "lang": "py.py3",
            "pid": 1001,
            "domainId": "system",
            "score": 100,
            "time": 160.0,
            "memory": 410,
            "judgeTexts": [],
            "compilerTexts": [],
            "testCases": [],
            "judger": 1,
            "judgeAt": datetime.utcnow(),
            "rejudged": False,
            "contest": contest_id,
            "files": {},
            "subtasks": {},
        },
        {
            "_id": ObjectId(),
            "status": SubmissionStatus.ACCEPTED,
            "uid": 23,
            "code": """
def greet():
    message = "Hello World!"
    print(message)
    return "completed"

if __name__ == "__main__":
    greet()
""",
            "lang": "python.python3",
            "pid": 1001,
            "domainId": "system",
            "score": 100,
            "time": 155.0,
            "memory": 405,
            "judgeTexts": [],
            "compilerTexts": [],
            "testCases": [],
            "judger": 1,
            "judgeAt": datetime.utcnow(),
            "rejudged": False,
            "contest": contest_id,
            "files": {},
            "subtasks": {},
        },
    ]

    # Insert submissions into database
    result = await db.record.insert_many(submissions)
    print(f"Inserted {len(result.inserted_ids)} demo submissions")

    return str(contest_id)


async def test_plagiarism_check(contest_id: str):
    """Test plagiarism check functionality."""
    print(f"\nTesting plagiarism check for contest: {contest_id}")

    # Create services
    db = await get_database()
    jplag_service = JPlagService(settings.jplag_jar_path)
    hydro_service = HydroService(db, jplag_service)

    # Create request
    request = ContestPlagiarismRequest(
        contest_id=contest_id, min_tokens=5, similarity_threshold=0.0
    )

    try:
        # Run plagiarism check
        result = await hydro_service.check_contest_plagiarism(request)

        print("Plagiarism check completed successfully!")
        print(f"Analysis ID: {result.analysis_id}")
        print(f"Total submissions: {result.total_submissions}")
        print(f"Total comparisons: {result.total_comparisons}")
        print(f"Execution time: {result.execution_time_ms}ms")
        print(f"High similarity pairs: {len(result.high_similarity_pairs)}")
        print(f"Clusters found: {len(result.clusters)}")

        if result.high_similarity_pairs:
            print("\nHigh similarity pairs:")
            for pair in result.high_similarity_pairs[:3]:  # Show first 3
                print(f"  {pair['first_submission']} vs {pair['second_submission']}")
                print(f"  Similarities: {pair['similarities']}")

        return result

    except Exception as e:
        print(f"Plagiarism check failed: {e}")
        return None


async def cleanup_demo_data(contest_id: str):
    """Clean up demo data."""
    db = await get_database()

    # Delete submissions
    result = await db.record.delete_many({"contest": ObjectId(contest_id)})
    print(f"\nCleaned up {result.deleted_count} demo submissions")

    # Delete plagiarism results
    result = await db.check_plagiarism_results.delete_many({"contest_id": contest_id})
    print(f"Cleaned up {result.deleted_count} plagiarism results")


async def main():
    """Main demo function."""
    print("=== Hydro OJ Integration Demo ===")

    # Check if JPlag is available
    if not os.path.exists(settings.jplag_jar_path):
        print(f"Warning: JPlag JAR not found at {settings.jplag_jar_path}")
        print("This demo will fail without JPlag. Please ensure JPlag is available.")

    try:
        # Create demo data
        contest_id = await create_demo_data()

        # Test plagiarism check
        result = await test_plagiarism_check(contest_id)

        if result:
            print("\nDemo completed successfully!")
            print(f"Result saved to database with analysis ID: {result.analysis_id}")
        else:
            print("\nDemo failed during plagiarism check")

        # Clean up
        cleanup = input("\nClean up demo data? (y/N): ")
        if cleanup.lower() == "y":
            await cleanup_demo_data(contest_id)
        else:
            print(f"Demo data preserved. Contest ID: {contest_id}")

    except Exception as e:
        print(f"Demo failed: {e}")
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
