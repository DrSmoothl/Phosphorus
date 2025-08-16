"""Example usage of JPlag API."""

import asyncio
import tempfile
from pathlib import Path

from src.api.jplag_models import PlagiarismAnalysisRequest, ProgrammingLanguage
from src.services.jplag_service import JPlagService


async def example_jplag_usage():
    """Example of using JPlag service."""
    # Initialize service
    service = JPlagService("lib/jplag-6.2.0.jar")

    # Create sample Java files
    with tempfile.TemporaryDirectory() as temp_dir:
        submission_dir = Path(temp_dir) / "submissions"
        submission_dir.mkdir()

        # Create first submission
        sub1_dir = submission_dir / "submission1"
        sub1_dir.mkdir()
        (sub1_dir / "Main.java").write_text("""
public class Main {
    public static void main(String[] args) {
        System.out.println("Hello World");
        int x = 5;
        int y = 10;
        int sum = x + y;
        System.out.println("Sum: " + sum);
    }
}
""")

        # Create second submission (very similar)
        sub2_dir = submission_dir / "submission2"
        sub2_dir.mkdir()
        (sub2_dir / "Main.java").write_text("""
public class Main {
    public static void main(String[] args) {
        System.out.println("Hello Universe");
        int a = 5;
        int b = 10;
        int result = a + b;
        System.out.println("Result: " + result);
    }
}
""")

        # Create third submission (different)
        sub3_dir = submission_dir / "submission3"
        sub3_dir.mkdir()
        (sub3_dir / "Main.java").write_text("""
public class Calculator {
    private int value;
    
    public Calculator(int initial) {
        this.value = initial;
    }
    
    public int add(int x) {
        return value + x;
    }
    
    public static void main(String[] args) {
        Calculator calc = new Calculator(0);
        System.out.println(calc.add(15));
    }
}
""")

        # Create request
        request = PlagiarismAnalysisRequest(
            language=ProgrammingLanguage.JAVA,
            min_tokens=5,
            similarity_threshold=0.0,
        )

        try:
            # Run JPlag analysis
            print("Running JPlag analysis...")
            result_file = await service._run_jplag(
                str(submission_dir), request, temp_dir, "example"
            )

            print(f"Analysis complete. Result file: {result_file}")

            # Parse results
            result = await service._parse_jplag_results(result_file, "example", request)

            print(f"Total submissions: {result.total_submissions}")
            print(f"Total comparisons: {result.total_comparisons}")
            print(f"Execution time: {result.execution_time_ms}ms")

            print("\nHigh similarity pairs:")
            for pair in result.high_similarity_pairs:
                avg_sim = pair.similarities.get("AVG", 0)
                if avg_sim > 0.3:  # Show pairs with >30% similarity
                    print(
                        f"  {pair.first_submission} vs {pair.second_submission}: {avg_sim:.2f}"
                    )

            print(f"\nClusters found: {len(result.clusters)}")
            for cluster in result.clusters:
                print(
                    f"  Cluster {cluster.index}: {cluster.members} (avg: {cluster.average_similarity:.2f})"
                )

        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    asyncio.run(example_jplag_usage())
